import math
import random

class Node:
    def __init__(self, func_unit, parent=None):
        self.func_unit = func_unit
        self.parent = parent
        self.children = []
        self.visits = 0
        self.success_count = 0

    def update(self, success_count):
        self.success_count += success_count
        self.visits += 1
        

class MCTS:
    def __init__(self, goal_node, kitchen_items, utensils, motion_nodes, foon_object_nodes, foon_object_to_FU_map, foon_functional_units, root_idx):
        self.goal_node = goal_node
        self.kitchen_items = kitchen_items
        self.motion_nodes=motion_nodes
        self.utensils=utensils
        self.foon_object_nodes=foon_object_nodes
        self.foon_object_to_FU_map=foon_object_to_FU_map
        self.foon_functional_units=foon_functional_units
        self.root = Node(foon_functional_units[root_idx])

    def selection(self, node, total_simulations):
        # Select the child with the highest UCB1 score
        def ucb1(child):
            if child.visits == 0:
                return float('inf')  # Encourage exploration of unvisited nodes
            exploitation = child.success_count / child.visits
            exploration = 2 * math.sqrt(math.log(total_simulations) / child.visits)
            return exploitation + exploration

        return max(node.children, key=ucb1)

    def expansion(self, node):
        # Expand by searching for functional units that can produce the input nodes
        for child in node.func_unit.input_nodes:
            child_idx=child.id
            flag = True
            if child.label in self.utensils and len(child.ingredients) == 1:
                for node2 in node.func_unit.input_nodes:
                    if node2.label == child.ingredients[
                            0] and node2.container == child.label:

                        flag = False
                        break
            if flag and not check_if_exist_in_kitchen(self.kitchen_items, child):
                for child_fu in self.foon_object_to_FU_map[child_idx]:
                    child_node = Node(self.foon_functional_units[child_fu], node)
                    node.children.append(child_node)
        return node.children
    
    def find_fu_for_input(self, input_node):
        # Find the functional unit that produces the input node
        candidate_units = self.foon_object_to_FU_map[input_node]

        if candidate_units:
            return candidate_units
        return None
    
    def simulate_subgraph(self, node, k):
        # Simulate k executions of the subgraph producing object i (node.state)
        success_count = 0
        for _ in range(k):
            if self.run_simulation(node):  # Perform one simulation
                success_count += 1
        return success_count

    def run_simulation(self, node):
        steps = 0
        max_steps = 100
        current_func_unit = node.func_unit
        while steps < max_steps:
            all_inputs_in_kitchen = True
            for current_item in current_func_unit.input_nodes:
                all_inputs_in_kitchen=all_inputs_in_kitchen and check_if_exist_in_kitchen(self.kitchen_items, current_item)
            if all_inputs_in_kitchen:
                return True  # Simulation succeeds if all inputs are available in the kitchen
            current_input_nodes=[]
            for child in current_func_unit.input_nodes:
                child_idx=child.id
                flag = True
                if child.label in self.utensils and len(child.ingredients) == 1:
                    for node2 in current_func_unit.input_nodes:
                        if node2.label == child.ingredients[
                                0] and node2.container == child.label:

                            flag = False
                            break
                if flag and not check_if_exist_in_kitchen(self.kitchen_items, child):
                    current_input_nodes.append(child_idx)
                        
            if not current_input_nodes:
                return False
            
            random_input = random.choice(current_input_nodes)
            new_fu_idx = random.choice(self.find_fu_for_input(random_input))

            # Check motion success or failure using motion success rate
            motion_success = self.check_motion_success(new_fu_idx)
            if not motion_success:
                return False  # Motion failure detected, terminate simulation

            if new_fu_idx:
                current_func_unit = self.foon_functional_units[new_fu_idx]
                steps += 1
            else:
                return False  # Fail the simulation if no FU can produce the required input

        return False  # If max steps are reached without success

    def check_motion_success(self, fu):
        # Get the motion success rate from the motion.txt data
        motion = self.foon_functional_units[fu].motion_node
        success_rate = self.motion_nodes[motion] 
        return random.random() < success_rate  # Simulate success or failure based on success rate

    def backpropagation(self, node, success_count):
        # Backpropagate the result up the tree
        while node is not None:
            node.update(success_count)
            node = node.parent

    def run(self, iterations, k):
        total_simulations = 0
        for _ in range(iterations):
            total_simulations += 1
            node = self.root

            # Selection
            while node.children:
                node = self.selection(node, total_simulations)

            # Expansion
            if node.visits > 0:  # Expand only visited nodes
                self.expansion(node)

            # Simulate k executions for each subgraph (functional unit)
            success_count = self.simulate_subgraph(node, k)

            # Backpropagation
            self.backpropagation(node, success_count)

            #print_tree(self.root)

        return node.success_count



def check_if_exist_in_kitchen(kitchen_items, ingredient):
    """
        parameters: a list of all kitchen items,
                    an ingredient to be searched in the kitchen
        returns: True if ingredient exists in the kitchen
    """

    for item in kitchen_items:
        if item["label"] == ingredient.label \
                and sorted(item["states"]) == sorted(ingredient.states) \
                and sorted(item["ingredients"]) == sorted(ingredient.ingredients) \
                and item["container"] == ingredient.container:
            return True

    return False

# Output tree structure for debugging
def print_tree(node, depth=0):
    print(f"{' ' * depth}Node: {node.func_unit.id}, Visits: {node.visits}, Successes: {node.success_count}")
    for child in node.children:
        print_tree(child, depth + 2)