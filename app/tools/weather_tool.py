"""Weather tool for weather-related queries using OpenWeather API."""

import re
from typing import Dict, Any, Optional
import httpx
from app.tools.base import BaseTool
from app import config


class WeatherTool(BaseTool):
    """Tool for weather information and forecasts."""

    def __init__(self):
        """Initialize the weather tool."""
        super().__init__("weather")
        self.client = httpx.AsyncClient(timeout=config.AGENT_TIMEOUT)
        self.openweather_api_key = config.OPENWEATHER_API_KEY
        self.openweather_base_url = config.OPENWEATHER_BASE_URL
        self.default_location = config.DEFAULT_LOCATION

        # For LLM-based location extraction
        self.llm_client = httpx.AsyncClient(timeout=config.AGENT_TIMEOUT)
        self.lm_studio_url = config.LM_STUDIO_BASE_URL
        self.lm_studio_model = config.LM_STUDIO_MODEL
        self.lm_studio_api_key = config.LM_STUDIO_API_KEY

    async def execute(self, query: str) -> str:
        """
        Execute weather query.

        Args:
            query: The user's weather-related query

        Returns:
            Weather information as a formatted string
        """
        import logging
        import time

        logger = logging.getLogger("ai_agent.weather")

        if not self.openweather_api_key:
            logger.error("Weather API key not configured")
            return (
                "Weather service is not configured. "
                "Please set the OPENWEATHER_API_KEY environment variable."
            )

        try:
            # Extract location using LLM
            start_time = time.time()
            location = await self._extract_location_with_llm(query)
            location_duration = time.time() - start_time

            if not location:
                location = self.default_location
                logger.info(
                    "Using default location",
                    extra={
                        "location": location,
                        "event": "default_location_used",
                    },
                )
            else:
                logger.info(
                    "Location extracted",
                    extra={
                        "location": location,
                        "duration": f"{location_duration:.3f}s",
                        "event": "location_extracted",
                    },
                )

            # Get weather data directly using city name
            api_start = time.time()
            weather_data = await self._get_weather_by_city(location)
            api_duration = time.time() - api_start

            if not weather_data:
                logger.warning(
                    "Weather data retrieval failed",
                    extra={
                        "location": location,
                        "duration": f"{api_duration:.3f}s",
                        "event": "weather_api_failed",
                    },
                )
                return (
                    f"Sorry, I couldn't retrieve weather data for {location}. "
                    "Please check the location name and try again."
                )

            logger.info(
                "Weather data retrieved",
                extra={
                    "location": location,
                    "duration": f"{api_duration:.3f}s",
                    "event": "weather_data_retrieved",
                },
            )

            # Convert technical data to natural language using LLM
            llm_start = time.time()
            natural_response = await self._convert_to_natural_language(
                weather_data, location, query
            )
            llm_duration = time.time() - llm_start

            if natural_response:
                logger.info(
                    "Natural language conversion completed",
                    extra={
                        "location": location,
                        "duration": f"{llm_duration:.3f}s",
                        "event": "natural_language_converted",
                    },
                )
                return natural_response
            else:
                # Fallback to technical format if LLM fails
                logger.warning(
                    "Natural language conversion failed, using fallback",
                    extra={
                        "location": location,
                        "event": "natural_language_fallback",
                    },
                )
                return self._format_weather_response(weather_data, location)

        except Exception as e:
            logger.error(
                "Weather query execution failed",
                extra={
                    "query": query,
                    "error": str(e),
                    "event": "weather_execution_failed",
                },
            )
            return f"Error getting weather information: {str(e)}"

    async def _extract_location_with_llm(self, query: str) -> Optional[str]:
        """
        Extract location from weather query using LLM.

        Args:
            query: The user's query

        Returns:
            Extracted location or None
        """
        try:
            # Prepare the prompt for location extraction
            system_prompt = """You are a location extraction assistant. Your job is to extract the location name from weather-related queries.

Extract the location and respond in JSON format:
{"location": "location_name"} or {"location": null}

Rules:
1. Extract only the location name (city, country, or region)
2. If no location is mentioned, return {"location": null}
3. Be specific - prefer city names over general regions when possible
4. Handle variations like "NYC" -> "New York City"
5. For country+city, prefer just the city: "Tokyo, Japan" -> "Tokyo"

Examples:
- "What's the weather in Paris?" -> {"location": "Paris"}
- "How's the weather in New York City today?" -> {"location": "New York City"}
- "Weather forecast for Tokyo, Japan" -> {"location": "Tokyo"}
- "Is it raining in London?" -> {"location": "London"}
- "What's the temperature?" -> {"location": null}
- "Weather in NYC" -> {"location": "New York City"}
- "How hot is it in the City of Angels?" -> {"location": "Los Angeles"}"""

            user_prompt = (
                f"Extract the location from this weather query: {query}"
            )

            # Call LM Studio
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.lm_studio_api_key}",
            }

            payload = {
                "model": self.lm_studio_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.0,  # Low temperature for consistent extraction
                "max_tokens": 100,
                "stream": False,
            }

            response = await self.llm_client.post(
                f"{self.lm_studio_url}/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                if (
                    data.get("choices")
                    and len(data["choices"]) > 0
                    and data["choices"][0].get("message")
                ):

                    llm_response = data["choices"][0]["message"][
                        "content"
                    ].strip()

                    # Parse JSON response
                    import json

                    try:
                        location_data = json.loads(llm_response)
                        extracted_location = location_data.get("location")

                        if (
                            extracted_location
                            and extracted_location.lower()
                            not in ["null", "none"]
                        ):
                            return extracted_location
                        else:
                            return None

                    except json.JSONDecodeError:
                        print(f"Invalid JSON from LLM: {llm_response}")
                        # Try to extract location from non-JSON response as fallback
                        if llm_response.lower() not in [
                            "none",
                            "null",
                            "unknown",
                        ]:
                            return llm_response
                        return None

            # Fallback to manual extraction if LLM fails
            print("LLM location extraction failed, using fallback")
            return self._extract_location_manual(query)

        except Exception as e:
            print(f"Error in LLM location extraction: {e}")
            # Fallback to manual extraction
            return self._extract_location_manual(query)

    def _extract_location_manual(self, query: str) -> Optional[str]:
        """
        Fallback manual location extraction.

        Args:
            query: The user's query

        Returns:
            Extracted location or None
        """
        query_lower = query.lower()

        # Remove common weather words
        weather_words = [
            "weather",
            "temperature",
            "forecast",
            "climate",
            "what's",
            "what is",
            "how's",
            "how is",
            "the",
            "in",
            "at",
            "for",
            "today",
            "tomorrow",
            "like",
        ]

        # Clean the query
        cleaned_query = query_lower
        for word in weather_words:
            cleaned_query = re.sub(rf"\b{word}\b", "", cleaned_query)

        # Remove extra spaces and punctuation
        cleaned_query = re.sub(r"[^\w\s]", "", cleaned_query)
        cleaned_query = " ".join(cleaned_query.split())

        if cleaned_query.strip():
            return cleaned_query.strip().title()

        return None

    async def _get_weather_by_city(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Get weather data from OpenWeather API using city name.

        Args:
            city: City name

        Returns:
            Weather data dictionary or None
        """
        try:
            params = {
                "q": city,
                "appid": self.openweather_api_key,
                "units": "metric",  # Use Celsius
            }

            response = await self.client.get(
                f"{self.openweather_base_url}/weather", params=params
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"City '{city}' not found")
                return None
            elif response.status_code == 401:
                print("OpenWeather API key invalid or not activated")
                return None
            else:
                print(
                    f"OpenWeather API error: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            print(f"Weather API error: {e}")
            return None

    async def _convert_to_natural_language(
        self, weather_data: Dict[str, Any], location: str, original_query: str
    ) -> Optional[str]:
        """
        Convert technical weather data to natural language using LLM.

        Args:
            weather_data: Raw weather data from API
            location: Location name
            original_query: User's original question

        Returns:
            Natural language weather response or None if LLM fails
        """
        try:
            # Extract key weather information
            temp = weather_data["main"]["temp"]
            feels_like = weather_data["main"]["feels_like"]
            humidity = weather_data["main"]["humidity"]
            description = weather_data["weather"][0]["description"]
            wind_speed = weather_data.get("wind", {}).get("speed", 0)
            pressure = weather_data["main"].get("pressure")
            visibility = weather_data.get("visibility")

            # Prepare the data for LLM
            weather_summary = {
                "location": location,
                "temperature": f"{temp:.1f}°C",
                "feels_like": f"{feels_like:.1f}°C",
                "conditions": description.title(),
                "humidity": f"{humidity}%",
                "wind_speed": f"{wind_speed} m/s",
                "pressure": f"{pressure} hPa" if pressure else "N/A",
                "visibility": (
                    f"{visibility/1000:.1f} km" if visibility else "N/A"
                ),
            }

            # Create LLM prompt for natural response
            system_prompt = """You are a friendly weather assistant. Convert technical weather data into natural, conversational responses.

Guidelines:
1. Be conversational and human-like
2. Answer the user's specific question if possible
3. Include relevant details but don't overwhelm with data
4. Use friendly language and appropriate tone
5. Mention if conditions are good/bad for activities
6. Keep it concise but informative
7. Respond in JSON format: {"response": "your_natural_answer"}

Examples:
- For "What's the weather in Paris?": "It's quite pleasant in Paris right now! The temperature is 22°C with partly cloudy skies. Perfect weather for a stroll along the Seine!"
- For "Is it raining in London?": "No rain in London at the moment! It's 18°C with overcast skies, so you might want to bring a light jacket just in case."
- For "How hot is it in Dubai?": "It's pretty warm in Dubai today at 35°C, feeling like 38°C with the humidity. Definitely stay hydrated and stick to air-conditioned spaces!"
"""

            user_prompt = f"""Original question: "{original_query}"
Location: {location}
Weather data: {weather_summary}

Please provide a natural, conversational response to the user's weather question."""

            # Call LLM
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.lm_studio_api_key}",
            }

            payload = {
                "model": self.lm_studio_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,  # Higher for more natural responses
                "max_tokens": 200,
                "stream": False,
            }

            response = await self.llm_client.post(
                f"{self.lm_studio_url}/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                if (
                    data.get("choices")
                    and len(data["choices"]) > 0
                    and data["choices"][0].get("message")
                ):

                    llm_response = data["choices"][0]["message"][
                        "content"
                    ].strip()

                    # Parse JSON response
                    import json

                    try:
                        response_data = json.loads(llm_response)
                        return response_data.get("response", llm_response)

                    except json.JSONDecodeError:
                        # Fallback to raw response if JSON parsing fails
                        return llm_response

            return None

        except Exception as e:
            print(f"Error in natural language conversion: {e}")
            return None

    def _format_weather_response(
        self, weather_data: Dict[str, Any], location: str
    ) -> str:
        """
        Format weather data into a readable response.

        Args:
            weather_data: Weather data from API
            location: Location name

        Returns:
            Formatted weather string
        """
        try:
            # Extract weather information
            temp = weather_data["main"]["temp"]
            feels_like = weather_data["main"]["feels_like"]
            humidity = weather_data["main"]["humidity"]
            description = weather_data["weather"][0]["description"].title()

            # Optional fields
            wind_speed = weather_data.get("wind", {}).get("speed", 0)
            pressure = weather_data["main"].get("pressure")
            visibility = weather_data.get("visibility")

            # Build response
            response = f"🌤️ Weather in {location}:\n"
            response += (
                f"🌡️ Temperature: {temp:.1f}°C "
                f"(feels like {feels_like:.1f}°C)\n"
            )
            response += f"☁️ Conditions: {description}\n"
            response += f"💧 Humidity: {humidity}%\n"

            if wind_speed > 0:
                response += f"💨 Wind Speed: {wind_speed} m/s\n"

            if pressure:
                response += f"📊 Pressure: {pressure} hPa\n"

            if visibility:
                visibility_km = visibility / 1000
                response += f"👁️ Visibility: {visibility_km:.1f} km\n"

            return response.strip()

        except KeyError as e:
            return f"Error parsing weather data: missing field {e}"
