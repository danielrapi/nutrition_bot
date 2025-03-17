from typing import Tuple, Dict, Optional
from app.models.user_profile import UserProfile
from app.services.simple_storage import SimpleStorage
from crewai import Agent, Task, Crew, LLM
from textwrap import dedent

class OnboardingService:
    def __init__(self, llm: LLM, storage: SimpleStorage):
        self.llm = llm
        self.storage = storage
        self.onboarding_agent = self._create_onboarding_agent()
        self.onboarding_steps = [
            'welcome',  # Welcome message + explain onboarding
            'height',   # Ask about height
            'weight',   # Ask about weight
            'age',      # Ask about age
            'activity', # Ask about activity level
            'goal',     # Ask about goals
            'complete'  # Onboarding complete
        ]
    
    def _create_onboarding_agent(self) -> Agent:
        """Create the onboarding agent"""
        return Agent(
            role='Nutrition Onboarding Specialist',
            goal='Guide users through onboarding with concise messages',
            backstory=dedent("""
                You are a friendly nutrition specialist who helps new users get started.
                You guide them through providing their information and goals,
                then calculate their calorie needs.
                
                ALWAYS keep responses under 1500 characters. Be concise and direct.
                Use bullet points when possible to save space.
                
                Always be encouraging, positive, and helpful.
            """),
            allow_delegation=False,
            verbose=True,
            llm=self.llm
        )
        
    async def process_message(self, user_id: str, message: str) -> Tuple[str, Optional[Dict]]:
        """
        Process incoming messages for onboarding
        Returns (response_text, updates_dict)
        """
        # Get or create user profile
        profile = await self.storage.get_user_profile(user_id)
        
        # For new users, create profile and send welcome message
        if not profile:
            profile = UserProfile(user_id=user_id)
            await self.storage.save_user_profile(profile)
            
            # Send welcome message and first question
            welcome_message = dedent("""
                👋 Welcome to your personalized nutrition assistant! 
                
                I'll help you reach your health and fitness goals, but first I need to learn a bit about you.
                
                Let's start: What's your height? (You can use cm, meters, feet/inches - I understand them all!)
            """)
            
            return welcome_message, None
        
        # If onboarding is already complete, respond accordingly
        if profile.is_onboarding_complete():
            return "Your profile is already set up! How can I help you today?", None
        
        # Determine current onboarding step
        current_step = self._get_current_step(profile)
        
        # Process the user's response based on current step
        return await self._process_step(current_step, message, profile)
        
    def _get_current_step(self, profile: UserProfile) -> str:
        """Determine which onboarding step we're on based on profile"""
        if profile.height is None:
            return 'height'
        elif profile.weight is None:
            return 'weight'
        elif profile.age is None:
            return 'age'
        elif profile.activity_level is None:
            return 'activity'
        elif profile.goal is None:
            return 'goal'
        else:
            return 'complete'
            
    async def _process_step(self, step: str, message: str, profile: UserProfile) -> Tuple[str, Optional[Dict]]:
        """Process the current onboarding step using the agent"""
        
        # Prepare agent description based on current step
        if step == 'height':
            task_desc = dedent(f"""
                The user is responding to a question about their height.
                Their response: "{message}"
                
                Extract the height value and convert to centimeters if needed.
                Valid heights for adults are typically between 100-250 cm (3'3" to 8'2").
                
                If you can extract a valid height:
                1. Return the height in cm as a number
                2. Provide a friendly confirmation and ask for their weight next
                
                If the input is unclear or invalid:
                1. Return "INVALID"
                2. Provide a friendly message asking them to share their height again
            """)
            
        elif step == 'weight':
            task_desc = dedent(f"""
                The user is responding to a question about their weight.
                Their response: "{message}"
                
                Extract the weight value and convert to kilograms if needed.
                Valid weights for adults are typically between 30-300 kg (66-660 lbs).
                
                If you can extract a valid weight:
                1. Return the weight in kg as a number
                2. Provide a friendly confirmation and ask for their age next
                
                If the input is unclear or invalid:
                1. Return "INVALID"
                2. Provide a friendly message asking them to share their weight again
            """)
            
        elif step == 'age':
            task_desc = dedent(f"""
                The user is responding to a question about their age.
                Their response: "{message}"
                
                Extract the age value.
                Valid ages are typically between 13-120 years.
                
                If you can extract a valid age:
                1. Return the age as a number
                2. Provide a friendly confirmation and ask about their activity level next
                
                If the input is unclear or invalid:
                1. Return "INVALID"
                2. Provide a friendly message asking them to share their age again
            """)
            
        elif step == 'activity':
            task_desc = dedent(f"""
                The user is responding to a question about their activity level.
                Their response: "{message}"
                
                Categorize their activity level into one of these categories:
                - sedentary (little to no exercise)
                - light (light exercise 1-3 days/week)
                - moderate (moderate exercise 3-5 days/week)
                - very_active (hard exercise 6-7 days/week)
                
                If you can determine their activity level:
                1. Return the activity level category
                2. Provide a friendly confirmation and ask about their goal next
                
                If the input is unclear:
                1. Return "INVALID"
                2. Ask them to select from the activity level options
            """)
            
        elif step == 'goal':
            task_desc = dedent(f"""
                The user is responding to a question about their primary fitness/nutrition goal.
                Their response: "{message}"
                
                Categorize their goal into one of these categories:
                - weight_loss
                - muscle_gain
                - maintenance
                
                If you can determine their goal:
                1. Return the goal category
                2. Provide a congratulatory message that onboarding is complete
                
                If the input is unclear:
                1. Return "INVALID"
                2. Ask them to clarify their primary goal
            """)
            
        elif step == 'complete':
            return await self._calculate_calorie_needs(profile), {'onboarding_complete': True}
            
        # Use the agent to process the step
        task = Task(
            description=task_desc,
            expected_output="Response with extracted value or INVALID",
            agent=self.onboarding_agent
        )
        
        crew = Crew(
            agents=[self.onboarding_agent],
            tasks=[task]
        )
        
        response = str(crew.kickoff()).strip()
        
        # Parse the agent's response
        if "INVALID" in response:
            # Invalid input, no updates to profile
            return response.replace("INVALID", "").strip(), None
        
        # Valid input, update profile
        updates = {}
        
        if step == 'height':
            # Extract height value from response
            for word in response.split():
                try:
                    height = float(word)
                    updates['height'] = height
                    break
                except ValueError:
                    continue
                    
        elif step == 'weight':
            # Extract weight value from response
            for word in response.split():
                try:
                    weight = float(word)
                    updates['weight'] = weight
                    break
                except ValueError:
                    continue
                    
        elif step == 'age':
            # Extract age value from response
            for word in response.split():
                try:
                    age = int(word)
                    updates['age'] = age
                    break
                except ValueError:
                    continue
                    
        elif step == 'activity':
            if 'sedentary' in response.lower():
                updates['activity_level'] = 'sedentary'
            elif 'light' in response.lower():
                updates['activity_level'] = 'light'
            elif 'moderate' in response.lower():
                updates['activity_level'] = 'moderate'
            elif 'very_active' in response.lower() or 'very active' in response.lower():
                updates['activity_level'] = 'very_active'
                
        elif step == 'goal':
            if 'weight_loss' in response.lower() or 'weight loss' in response.lower():
                updates['goal'] = 'weight_loss'
            elif 'muscle_gain' in response.lower() or 'muscle gain' in response.lower():
                updates['goal'] = 'muscle_gain'
            elif 'maintenance' in response.lower():
                updates['goal'] = 'maintenance'
                
            # If this is the final step and we got a valid response, mark onboarding as complete
            if any(goal in response.lower() for goal in ['weight_loss', 'weight loss', 'muscle_gain', 'muscle gain', 'maintenance']):
                updates['onboarding_complete'] = True
                
                # For the final step, we want to show the calorie calculation
                updated_profile = UserProfile(
                    user_id=profile.user_id,
                    height=profile.height,
                    weight=profile.weight,
                    age=profile.age,
                    activity_level=profile.activity_level,
                    goal=updates.get('goal', None),
                    onboarding_complete=True
                )
                
                calorie_response = await self._calculate_calorie_needs(updated_profile)
                return calorie_response, updates
        
        # Return the agent's response and any updates
        return response, updates
    
    async def _calculate_calorie_needs(self, profile: UserProfile) -> str:
        """Calculate calorie needs based on user profile"""
        task = Task(
            description=dedent(f"""
                Calculate daily calorie needs for user with:
                Height: {profile.height} cm
                Weight: {profile.weight} kg
                Age: {profile.age}
                Activity level: {profile.activity_level}
                Goal: {profile.goal}
                
                IMPORTANT: Keep your response under 1500 characters total!
                Be extremely concise and focused.
                
                Briefly explain:
                1. Their maintenance calories
                2. Their target calories based on goal
                3. Very brief macro recommendations
                
                Make your response concise but helpful.
            """),
            expected_output="Brief explanation under 1500 characters",
            agent=self.onboarding_agent
        )
        
        crew = Crew(
            agents=[self.onboarding_agent],
            tasks=[task]
        )
        
        return str(crew.kickoff()) 