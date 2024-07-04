"""

# logger.debug(f"d.keys(): {d.keys()}, dep: {dep}")
            for dep_id in task["dep"]:
                if dep_id >= task["id"]:
                    task["dep"] = [-1]
                    break
            dep = task["dep"]
            if dep[0] == -1 or len(list(set(dep).intersection(d.keys()))) == len(dep):
                tasks.remove(task)
                thread = threading.Thread(target=run_task, args=(input, task, d))
                thread.start()
                threads.append(thread)
        if num_thread == len(threads):
            time.sleep(0.5)
            retry += 1
        if retry > 160:
            logger.debug("User has waited too long, Loop break.")
            break
        if len(tasks) == 0:
            break
    for thread in threads:
        thread.join()

    results = d.copy()

    logger.debug(results)
    if return_results:
        return results

    response = response_results(input, results).strip()

    end = time.time()
    during = end - start

    answer = {"message": response}
    record_case(success=True,
                **{"input": input, "task": task_str, "results": results, "response": response, "during": during,
                   "op": "response"})
    logger.info(f"response: {response}")
    return answer
"""