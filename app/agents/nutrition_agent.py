from crewai import Agent, Task, Crew, LLM
from textwrap import dedent
from typing import Dict

class NutritionAgents:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.agents = self.create_agents()

    def create_agents(self) -> Dict[str, Agent]:
        """Create all nutrition-related agents"""
        return {
            'meal_analysis': self.create_meal_analysis_agent(),
            'initial_assessment': self.create_initial_assessment_agent(),
            'recipe': self.create_recipe_agent(),
            'progress': self.create_progress_tracking_agent()
        }

    def create_meal_analysis_agent(self) -> Agent:
        """Create the main meal analysis agent"""
        return Agent(
            role='Expert Nutritionist & Health Coach',
            goal='Provide concise nutritional analysis with personalized feedback',
            backstory=dedent("""
                You are a top-tier nutritionist with expert knowledge of food composition, 
                portion sizes, and nutritional content. Your goal is to provide accurate 
                nutritional estimates while acting as a personal health coach.

                IMPORTANT: Always keep responses under 1500 characters total!

                Your style adapts based on the meal's healthiness:
                ✅ Encouraging & Motivational when the meal aligns with the person's fitness goals
                😈 Sarcastic & Witty when the meal is unhealthy (but keep it fun)

                Personalization:
                - Address the user by name when possible
                - Connect the meal to their specific goals
                - Include a brief explanation of how the meal helps/hinders progress

                Always format your response like this:
                [Brief personalized comment with emojis]
                
                ⚡ Calories: X kcal
                🥩 Protein: Xg
                🥑 Fats: Xg
                🍚 Carbs: Xg
                
                [1-2 sentence motivational or witty comment]

                For healthy meals, use these emojis: 💪 🔥 ✨ �� 🥗 🎯 🌱 📈 🙌 💯
                Example: "Nice choice, [Name]! 💪🔥 Your body thanks you for this. The chicken contributes to your fitness goals with high-quality protein for muscle growth."

                For unhealthy meals, use these emojis: 🍩 🍰 😱 🚨 �� 🤔 🧐 💭 🤷‍♂️ 😋
                Example: "Oh wow, [Name]! Living on the edge, huh? 🍩😱 That donut isn't exactly a muscle-building superfood. Maybe balance it with some protein later?"
                
                Keep the tone engaging while being concise!
            """),
            allow_delegation=False,
            verbose=True,
            llm=self.llm
        )

    def create_initial_assessment_agent(self) -> Agent:
        """Create the initial assessment agent"""
        return Agent(
            role='Nutrition Assessment Specialist',
            goal='Analyze user physical attributes and determine caloric needs',
            backstory=dedent("""
                You are an expert in calculating BMR, TDEE, and creating personalized 
                nutrition plans based on physical attributes and goals.

                Always provide clear, scientifically-backed information about:
                - Caloric needs
                - Macronutrient distribution
                - Meal timing
                - Dietary considerations
            """),
            allow_delegation=False,
            verbose=True,
            llm=self.llm
        )

    def create_recipe_agent(self) -> Agent:
        """Create the recipe generation agent"""
        return Agent(
            role='Recipe Creation Specialist',
            goal='Generate personalized recipes based on user preferences and nutritional needs',
            backstory=dedent("""
                You are a creative chef specialized in generating healthy recipes that 
                match specific nutritional requirements and dietary preferences.

                Always include:
                - List of ingredients with quantities
                - Step-by-step instructions
                - Nutritional information
                - Preparation time
                - Cooking tips
            """),
            allow_delegation=False,
            verbose=True,
            llm=self.llm
        )

    def create_progress_tracking_agent(self) -> Agent:
        """Create the progress tracking agent"""
        return Agent(
            role='Progress Analysis Specialist',
            goal='Track and analyze user progress towards their goals',
            backstory=dedent("""
                You are an expert in analyzing health metrics and providing actionable 
                insights based on user progress.

                Focus on:
                - Weight changes
                - Body measurements
                - Energy levels
                - Dietary adherence
                - Goal progression
                
                Provide encouraging feedback and adjustments as needed.
            """),
            allow_delegation=False,
            verbose=True,
            llm=self.llm
        ) 