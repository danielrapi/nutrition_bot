from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display


import app.models as models
from app.agents.router import Router
from app.agents.meal_tracking import Meal_Tracker
from app.agents.synthesizer import Synthesizer

class Workflow:
    """Workflow class for the LangGraph flow"""
   
    def __init__(self):
        # Create the state graph with the State class as the schema
        self.graph = StateGraph(state_schema=models.State)
        
        # Initialize agents
        self.router = Router()
        self.meal_tracking_agent = Meal_Tracker()
        self.synthesizer = Synthesizer()
        # Initialize nodes
        self.graph.add_node("router", self.router)
        self.graph.add_node("meal_tracking_agent", self.meal_tracking_agent)
        self.graph.add_node("synthesizer", self.synthesizer)
        # Add edges
        self.graph.add_edge(START, "router")
        
        # Conditional edge based on whether the router set a response
        self.graph.add_conditional_edges(
            "router",
            lambda state: "meal_tracking_agent" if state.response is None else END,
        )

        self.graph.add_edge("meal_tracking_agent", "synthesizer")
        
        self.graph.add_edge("synthesizer", END)
        
        # Compile the graph
        self.compiled_graph = self.graph.compile()
        
    # Display graph
    def display_graph(self):
        display(Image(self.graph.draw_mermaid_png()))

    # Run graph with a state instance
    def run_graph(self, state_instance):
        """
        Run the workflow with a specific state instance
        
        Args:
            state_instance: An instance of the State class
            
        Returns: 
            Final state after running the workflow
        """
        print(f"Running graph with initial state: {state_instance}")
        result = self.compiled_graph.invoke(state_instance)
        #print(f"Graph result type: {type(result)}")
        #print(f"Graph result contents: {result}")
        return result