import xml.etree.ElementTree as ET
import itertools
import random
import os

XACML_NS = {"xacml": "urn:oasis:names:tc:xacml:3.0:core:schema:wd-17"}

# =====================================================
# DATA MODEL
# =====================================================
class Rule:
    def __init__(self, rule_id, effect, conditions):
        self.id = rule_id
        self.effect = effect
        self.conditions = conditions  # [(attr, category, value)]

class TestCase:
    def __init__(self, tc_id, attributes, covers):
        self.id = tc_id
        self.attributes = attributes  # attr -> (value, category)
        self.covers = set(covers)

    def __repr__(self):
        return f"TC{self.id}: {self.attributes} covers={self.covers}"


# =====================================================
# 1. PARSE POLICY
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

            conditions.append((
                designator.get("AttributeId"),
                designator.get("Category"),
                value
            ))

        rules.append(Rule(rule_id, effect, conditions))

    return rules


# =====================================================
# 2. ATTRIBUTE DOMAINS (for combinatorial generation)
# =====================================================
def build_attribute_domains(rules):
    domains = {}

    for rule in rules:
        for attr, cat, value in rule.conditions:
            domains.setdefault(attr, {
                "category": cat,
                "values": set()
            })
            domains[attr]["values"].add(value)

    # add extra values for negative / NotApplicable testing
    for attr in domains:
        domains[attr]["values"].add("UNKNOWN")

    return domains


# =====================================================
# 3. GENERATE TEST CASES (DFS / CARTESIAN PRODUCT)
# =====================================================
def generate_test_cases(rules):
    domains = build_attribute_domains(rules)

    attrs = list(domains.keys())
    value_sets = [list(domains[a]["values"]) for a in attrs]

    test_cases = []
    tc_id = 1

    for combination in itertools.product(*value_sets):
        attributes = {}
        covers = set()

        for attr, value in zip(attrs, combination):
            attributes[attr] = (value, domains[attr]["category"])

        # rule coverage check
        for rule in rules:
            if all(attributes.get(a, ("", ""))[0] == v
                   for a, _, v in rule.conditions):
                covers.add(rule.id)

        test_cases.append(TestCase(tc_id, attributes, covers))
        tc_id += 1

    return test_cases


# =====================================================
# 4. REQUEST BUILDER
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


def export_requests(test_cases, folder):
    os.makedirs(folder, exist_ok=True)

    for tc in test_cases:
        path = os.path.join(folder, f"request_{tc.id}.xml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_request_xml(tc.attributes))
        print(f"[EXPORT] request_{tc.id}.xml covers={tc.covers}")

    print(f"[OK] Exported {len(test_cases)} requests → {folder}")


# =====================================================
# 5. COVERAGE
# =====================================================
def rule_coverage(test_cases, all_rules):
    covered = set()
    for tc in test_cases:
        covered |= tc.covers
    return len(covered) / len(all_rules)


# =====================================================
# 6. GENETIC ALGORITHM (TEST MINIMIZATION)
# =====================================================
def fitness(individual, test_cases, all_rules,
            alpha=0.8, beta=0.2):

    selected = [tc for bit, tc in zip(individual, test_cases) if bit]
    if not selected:
        return 0

    cov = rule_coverage(selected, all_rules)
    penalty = len(selected) / len(test_cases)

    return alpha * cov - beta * penalty


def genetic_algorithm(test_cases, all_rules,
                      pop_size=20, generations=50):

    population = [
        [random.randint(0, 1) for _ in test_cases]
        for _ in range(pop_size)
    ]

    for _ in range(generations):
        population = sorted(
            population,
            key=lambda ind: fitness(ind, test_cases, all_rules),
            reverse=True
        )

        next_gen = population[:2]  # elitism

        while len(next_gen) < pop_size:
            p1, p2 = random.sample(population[:10], 2)
            point = random.randint(1, len(p1) - 1)
            child = p1[:point] + p2[point:]

            child = [
                1 - b if random.random() < 0.05 else b
                for b in child
            ]
            next_gen.append(child)

        population = next_gen

    return population[0]


# =====================================================
# 7. MAIN
# =====================================================
if __name__ == "__main__":

    rules = parse_policy("policy.xml")
    all_rules = {r.id for r in rules}

    test_cases = generate_test_cases(rules)
    print("Total generated test cases:", len(test_cases))
    print("Coverage before optimization:",
          rule_coverage(test_cases, all_rules))

    export_requests(test_cases, "requests_full")

    best = genetic_algorithm(test_cases, all_rules)
    optimized = [
        tc for bit, tc in zip(best, test_cases) if bit
    ]

    print("Optimized test cases:", len(optimized))
    print("Coverage after optimization:",
          rule_coverage(optimized, all_rules))

    export_requests(optimized, "requests_optimized")
