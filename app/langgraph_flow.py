from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display


import app.models as models
from app.agents.router import Router
from app.agents.meal_tracking import Meal_Tracker
from app.agents.synthesizer import Synthesizer
from app.agents.transcriber import Transcriber
from app.agents.summary import Summary_Creator

class Workflow:
    """Workflow class for the LangGraph flow"""
   
    def __init__(self):
        # Create the state graph with the State class as the schema
        self.graph = StateGraph(state_schema=models.State)
        
        # Initialize agents
        self.transcriber = Transcriber()
        self.router = Router()
        self.meal_tracking_agent = Meal_Tracker()
        self.synthesizer = Synthesizer()
        self.summary_creator = Summary_Creator()
        # Initialize nodes
        self.graph.add_node("transcriber", self.transcriber)
        self.graph.add_node("router", self.router)
        self.graph.add_node("meal_tracking_agent", self.meal_tracking_agent)
        self.graph.add_node("synthesizer", self.synthesizer)
        self.graph.add_node("summary_creator", self.summary_creator)

    
        # Add edges

        #Conditional edge based on whether the message contains audio
        self.graph.add_conditional_edges(
            START,
            # check if audio is present
            lambda state: len(state.message.media_items) > 0 and state.message.media_items[0]["type"].startswith("audio"),
            {True: "transcriber", False: "router"}
        )

        self.graph.add_edge("transcriber", "router")
        
        #Conditional edge based on whether the router set a response
        self.graph.add_conditional_edges(
            "router",
            lambda state: state.intent if state.intent else "other",  # Default to "other" if intent is None
            {
                "meal_tracking": "meal_tracking_agent", 
                "summary": "summary_creator", 
                "other": END
            }
        )
        self.graph.add_edge("meal_tracking_agent", "synthesizer")
        self.graph.add_edge("summary_creator", END)
        self.graph.add_edge("synthesizer", END)
        
        # Compile the graph
        self.compiled_graph = self.graph.compile()
        
    # Display graph
    def save_display_graph(self):
        #save png of graph
        self.compiled_graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

    # Run graph with a state instance
    async def run_graph(self, state_instance):
        """
        Run the workflow with a specific state instance
        
        Args:
            state_instance: An instance of the State class
            
        Returns: 
            Final state after running the workflow
        """
        #clip initial state to 100 characters
        print(f"Running graph with initial state: {str(state_instance)[:100]}...")
        result = await self.compiled_graph.ainvoke(state_instance)
        #print(f"Graph result type: {type(result)}")
        #print(f"Graph result contents: {result}")
        return result