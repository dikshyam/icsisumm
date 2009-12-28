import sys
sys.path.append('IR/')
import tfidf, util, prob_util, framework, concept_mapper


def make_query(problem):
    """
    """
    mapper = concept_mapper.HeuristicMapper(problem, 'n1')
    mapper.map_concepts()
    concepts = prob_util.Counter(mapper.concepts).sortedKeys()
    concepts = [c[0] for c in concepts]
    return concepts

def get_docs(task, num_docs, reload=False):
    """
    returns a new task, where each problem in task.problems has:
    problem.ir_docs = [ ... ]
    """
    
    ## check state
    if not reload and framework.check_state(task.problems)['ir']:
        sys.stderr.write('already have ir documents loaded\n')
        return task
    
    max_files = 0

    ## get all query tokens; use tfidf.get_tokens because this matches the index's tokenization
    queries_by_problem_id = {}
    for problem in task.problems:
        #curr_query = ' '.join(tfidf.get_tokens(problem.query.original))
        curr_query = ' '.join(make_query(problem))
        queries_by_problem_id[problem.id] = curr_query
        
    ## do the search
    all_queries = queries_by_problem_id.values()
    docs_by_query = tfidf.search(tfidf.file_index_pickle_path, all_queries, tfidf.search_cmd, max_files, num_docs)

    ## for debugging
    docfh = open('irdoc_debug', 'w')
    
    ## allocate docs to problems
    for problem in task.problems:
        query = queries_by_problem_id[problem.id]
        docs_with_values = docs_by_query[query]

        ## inspect values for debugging
        docfh.write('# problem [%s]\n' %problem.id)
        for doc, val in docs_with_values:
            docfh.write('## doc_id [%s]  value [%1.4f]\n' %(doc.id, float(val)))
            for par in doc.paragraphs:
                docfh.write('%s\n' %par)

        ## sentence segmentation
        docs = [doc for doc, val in docs_with_values]
        for doc in docs: doc.get_sentences()
        
        problem.ir_docs = docs
        problem.loaded_ir_docs = True
        
    ## pickle it up
    sys.stderr.write('Saving [%s] problem data in [%s]\n' %(task.name, task.data_pickle))
    util.save_pickle(task.problems, task.data_pickle)
    return task
