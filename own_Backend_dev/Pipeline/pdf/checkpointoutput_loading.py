
import pickle
pkl_dir = r"D:\MultiModulRag\Backend_dev\Database\Pickel\output.pkl"
with open(pkl_dir, 'rb') as f:
    loaded_docs = pickle.load(f)

# Now this will work:
print(f"📄 AI content produced: {loaded_docs[0].page_content[:200]}...")
print(f"📊 Metadata: {loaded_docs[0].metadata}")