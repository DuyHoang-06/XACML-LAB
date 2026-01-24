"""
Module: xacml_test_optimization.py

Pipeline:
1. DFS traversal → full test suite
2. Coverage measurement
3. Genetic Algorithm optimization
4. Coverage evaluation after optimization
"""

import random

# ==================================================
# 1. DATA STRUCTURE: TEST CASE
# ==================================================

class TestCase:
    def __init__(self, tc_id, attributes, covers):
        self.id = tc_id
        self.attributes = attributes      # e.g., {"role": "manager"}
        self.covers = set(covers)          # rules covered

    def __repr__(self):
        return f"TC{self.id}{self.attributes}"


# ==================================================
# 2. DFS GENERATION (SIMULATED FROM XACML)
# ==================================================

def dfs_generate_test_cases():
    """
    Simulate DFS traversal over XACML policy graph
    """
    test_cases = [
        TestCase(1, {"role": "manager"}, {"rule-1"}),
        TestCase(2, {"role": "guest"}, {"rule-2"}),
        TestCase(3, {"role": "staff"}, set())  # NotApplicable
    ]
    return test_cases

# =====================================================
# 3. BUILD REQUEST.XML
# =====================================================
def build_request_xml(attributes):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<Request>']

    for attr, value in attributes.items():
        xml.append(f'''
  <Attributes Category="subject">
    <Attribute AttributeId="{attr}">
      <AttributeValue>{value}</AttributeValue>
    </Attribute>
  </Attributes>''')

    xml.append('</Request>')
    return "\n".join(xml)


def export_requests(test_cases, folder):
    os.makedirs(folder, exist_ok=True)

    for tc in test_cases:
        content = build_request_xml(tc.attributes)
        file_path = os.path.join(folder, f"request_{tc.id}.xml")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[OK] Exported {len(test_cases)} requests to '{folder}'")

# ==================================================
# 3. COVERAGE METRICS
# ==================================================

def rule_coverage(selected_tests, all_rules):
    if not selected_tests:
        return 0.0

    covered = set()
    for tc in selected_tests:
        covered |= tc.covers

    return len(covered) / len(all_rules)


# ==================================================
# 4. GENETIC ALGORITHM
# ==================================================

def fitness(individual, test_cases, all_rules,
            alpha=0.8, beta=0.2):
    selected = [
        tc for bit, tc in zip(individual, test_cases) if bit == 1
    ]

    if not selected:
        return 0

    coverage = rule_coverage(selected, all_rules)
    size_penalty = len(selected) / len(test_cases)

    return alpha * coverage - beta * size_penalty


def random_individual(length):
    return [random.randint(0, 1) for _ in range(length)]


def select_best(population, test_cases, all_rules):
    return max(
        population,
        key=lambda ind: fitness(ind, test_cases, all_rules)
    )


def crossover(p1, p2):
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:]


def mutate(individual, rate=0.1):
    return [
        1 - bit if random.random() < rate else bit
        for bit in individual
    ]


def genetic_algorithm(test_cases, all_rules,
                      pop_size=10, generations=30):
    population = [
        random_individual(len(test_cases))
        for _ in range(pop_size)
    ]

    for _ in range(generations):
        new_population = []
        for _ in range(pop_size):
            p1 = select_best(population, test_cases, all_rules)
            p2 = select_best(population, test_cases, all_rules)

            child = crossover(p1, p2)
            child = mutate(child)

            new_population.append(child)

        population = new_population

    best = select_best(population, test_cases, all_rules)
    return best


# ==================================================
# 5. MAIN PIPELINE
# ==================================================

if __name__ == "__main__":

    print("=== DFS: Generate Full Test Suite ===")
    test_cases = dfs_generate_test_cases()
    for tc in test_cases:
        print(tc)

    all_rules = {"rule-1", "rule-2"}

    print("\n=== Coverage Before Optimization ===")
    cov_before = rule_coverage(test_cases, all_rules)
    print("Rule Coverage:", cov_before)
    print("Total Test Cases:", len(test_cases))

    print("\n=== Run Genetic Algorithm Optimization ===")
    best_individual = genetic_algorithm(test_cases, all_rules)
    print("Best Individual:", best_individual)

    optimized_tests = [
        tc for bit, tc in zip(best_individual, test_cases) if bit == 1
    ]

    print("\n=== Optimized Test Suite ===")
    for tc in optimized_tests:
        print(tc)

    print("\n=== Coverage After Optimization ===")
    cov_after = rule_coverage(optimized_tests, all_rules)
    print("Rule Coverage:", cov_after)
    print("Total Test Cases:", len(optimized_tests))
