import utils.llm_initial_util as llm_initial

llm, embeddings = llm_initial.initialize_llm("Volcengine", "doubao-Seed-1.6-thinking", "doubao-embedding")
response = llm.invoke("你好，火山引擎！")
print(response)
