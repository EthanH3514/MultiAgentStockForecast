from sklearn.svm import SVC
import joblib

def build_model():
    """
    构建SVM分类模型用于预测股票涨跌
    """
    # 使用SVM分类器，选择RBF核函数
    model = SVC(
        kernel='rbf',  # 径向基函数核
        C=1.0,         # 正则化参数
        gamma='scale', # 核系数
        probability=True,  # 启用概率估计
        random_state=42
    )
    
    return model

def save_model(model, model_path='best_model.pkl'):
    """
    保存模型
    """
    joblib.dump(model, model_path)

def load_model(model_path='best_model.pkl'):
    """
    加载模型
    """
    return joblib.load(model_path)