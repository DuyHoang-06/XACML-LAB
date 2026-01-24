def generate_requests_from_paths(paths):
    requests = []
    for path in paths:
        attr = extract_condition(path)
        requests.append(build_request_xml(attr))
    return requests
