import xml.etree.ElementTree as ET
import random
import os

# =====================================================
# XACML NAMESPACE
# =====================================================
XACML_NS = {"xacml": "urn:oasis:names:tc:xacml:3.0:core:schema:wd-17"}

# =====================================================
# DATA STRUCTURE
# =====================================================
class TestCase:
    def __init__(self, tc_id, attributes, covers):
        self.id = tc_id
        self.attributes = attributes   # attr -> (value, category)
        self.covers = set(covers)

    def __repr__(self):
        return f"TC{self.id}{self.attributes}"



# =====================================================
# 1. PARSE XACML POLICY
# =====================================================
def parse_policy(policy_file):
    tree = ET.parse(policy_file)
    root = tree.getroot()

    rules = []

    for rule in root.findall("xacml:Rule", XACML_NS):
        rule_id = rule.get("RuleId")
        effect = rule.get("Effect")

        conditions = []

        for match in rule.findall(".//xacml:Match", XACML_NS):
            value = match.find("xacml:AttributeValue", XACML_NS).text
            designator = match.find("xacml:AttributeDesignator", XACML_NS)

            conditions.append({
                "attr": designator.get("AttributeId"),
                "category": designator.get("Category"),
                "value": value
            })

        rules.append({
            "rule_id": rule_id,
            "effect": effect,
            "conditions": conditions
        })

    return rules


# =====================================================
# 2. DFS → GENERATE TEST CASES
# =====================================================
def dfs_generate_test_cases(rules):
    test_cases = []
    tc_id = 1

    for rule in rules:
        attributes = {}

        for cond in rule["conditions"]:
            attributes[cond["attr"]] = (cond["value"], cond["category"])

        test_cases.append(
            TestCase(tc_id, attributes, {rule["rule_id"]})
        )
        tc_id += 1

    # NotApplicable test case
    test_cases.append(
        TestCase(tc_id, {"role": ("unknown", "subject")}, set())
    )

    return test_cases


# =====================================================
# 3. BUILD REQUEST.XML
# =====================================================
def build_request_xml(attributes):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<Request>']

    grouped = {}

    for attr, (value, category) in attributes.items():
        grouped.setdefault(category, []).append((attr, value))

    for category, items in grouped.items():
        xml.append(f'  <Attributes Category="{category}">')

        for attr, value in items:
            xml.append(f'''
    <Attribute AttributeId="{attr}">
      <AttributeValue>{value}</AttributeValue>
    </Attribute>''')

        xml.append('  </Attributes>')

    xml.append('</Request>')
    return "\n".join(xml)


# =====================================================
# 4. Export request
# =====================================================
def export_requests(test_cases, folder):
    os.makedirs(folder, exist_ok=True)

    for tc in test_cases:
        content = build_request_xml(tc.attributes)
        path = os.path.join(folder, f"request_{tc.id}.xml")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[EXPORT] request_{tc.id}.xml → covers {tc.covers}")

    print(f"[OK] Exported {len(test_cases)} requests to {folder}")

# =====================================================
# 5. COVERAGE
# =====================================================
def rule_coverage(test_cases, all_rules):
    covered = set()
    for tc in test_cases:
        covered |= tc.covers
    return len(covered) / len(all_rules)


# =====================================================
# 6. GENETIC ALGORITHM
# =====================================================
def fitness(individual, test_cases, all_rules,
            alpha=0.8, beta=0.2):
    selected = [
        tc for bit, tc in zip(individual, test_cases) if bit == 1
    ]
    if not selected:
        return 0

    cov = rule_coverage(selected, all_rules)
    size_penalty = len(selected) / len(test_cases)

    return alpha * cov - beta * size_penalty


def random_individual(n):
    return [random.randint(0, 1) for _ in range(n)]


def select_best(population, test_cases, all_rules):
    return max(
        population,
        key=lambda ind: fitness(ind, test_cases, all_rules)
    )


def crossover(p1, p2):
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:]


def mutate(ind, rate=0.1):
    return [
        1 - bit if random.random() < rate else bit
        for bit in ind
    ]


def genetic_algorithm(test_cases, all_rules,
                      pop_size=10, generations=30):
    population = [random_individual(len(test_cases))
                  for _ in range(pop_size)]

    for _ in range(generations):
        new_population = []
        for _ in range(pop_size):
            p1 = select_best(population, test_cases, all_rules)
            p2 = select_best(population, test_cases, all_rules)
            child = mutate(crossover(p1, p2))
            new_population.append(child)
        population = new_population

    return select_best(population, test_cases, all_rules)


# =====================================================
# 7. MAIN
# =====================================================
if __name__ == "__main__":

    rules = parse_policy("policy.xml")
    all_rules = {r["rule_id"] for r in rules}

    test_cases = dfs_generate_test_cases(rules)

    print("Coverage before GA:",
          rule_coverage(test_cases, all_rules))

    export_requests(test_cases, "requests_full")

    best = genetic_algorithm(test_cases, all_rules)
    optimized = [
        tc for bit, tc in zip(best, test_cases) if bit == 1
    ]

    print("Coverage after GA:",
          rule_coverage(optimized, all_rules))

    export_requests(optimized, "requests_optimized")

