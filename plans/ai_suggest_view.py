from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import openai

class AiSuggestView(APIView):
    """
    POST /api/ai/suggest/
    Request: { type: 'date'|'activity'|'itinerary', location, dates, preferences }
    Response: { suggestions: [{ type, text }] }
    """
    def post(self, request):
        data = request.data
        suggestion_type = data.get('type')
        location = data.get('location')
        dates = data.get('dates')
        preferences = data.get('preferences')

        # Example prompt template
        prompt = self.build_prompt(suggestion_type, location, dates, preferences)

        # Call LLM provider (placeholder)
        llm_response = self.call_llm(prompt)

        suggestions = self.parse_llm_response(llm_response, suggestion_type)
        return Response({ 'suggestions': suggestions }, status=status.HTTP_200_OK)

    def build_prompt(self, suggestion_type, location, dates, preferences):
        if suggestion_type == 'date':
            return f"Suggest best travel dates for {location} based on group availability: {dates}"
        elif suggestion_type == 'activity':
            return f"Suggest fun activities in {location} for these dates: {dates}. Preferences: {preferences}"
        elif suggestion_type == 'itinerary':
            return f"Generate a sample itinerary for {location} on {dates}. Preferences: {preferences}"
        return ""

    def call_llm(self, prompt):
        # Uses OpenAI GPT-3.5/4 for suggestions
        openai.api_key = getattr(settings, "OPENAI_API_KEY", None)
        if not openai.api_key:
            return "[OpenAI API key not set]"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful travel planning assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=256,
                n=1,
                temperature=0.7,
            )
            return response.choices[0].message["content"].strip()
        except Exception as e:
            return f"[OpenAI error: {e}]"

    def parse_llm_response(self, llm_response, suggestion_type):
        # Placeholder: Parse LLM response into structured suggestions
        return [{ 'type': suggestion_type, 'text': llm_response }]

# Add to urls.py:
# path('api/ai/suggest/', AiSuggestView.as_view()),
