import pickle

pkl_path = r"D:\MultiModulRag\Backend_dev\Database\Pickel\checkpoint1.pkl"
with open(pkl_path, "rb") as f:
        loaded1 = pickle.load(f)
print(f"✅ Load Pickel has : {len(loaded1)} elements")