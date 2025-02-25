import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


path_dict = {
    "qwen2.5-3b-instruct": "./qwen2.5-3b-instruct/qwen2.5-3b-instruct_res.npy",
    "qwen-turbo": "./qwen-turbo/qwen-turbo_res.npy",
    "r=4": "./r=4/checkpoint-1000/checkpoint-1000_res.npy",
    "r=8": "./r=8/checkpoint-1500/checkpoint-1500_res.npy",
}

if __name__ == "__main__":
    cmp_res = {}
    for k, v in path_dict.items():
        res = np.load(v, allow_pickle=True)
        # 对除最后一列外的列求和并除以 100：所有工具通用的评测
        partial_sum = np.sum(res[:, :-1], axis=0) / 100.0
        # 对最后一列求和并除以 40：特定工具的评测
        last_col_sum = np.sum(res[:, -1]) / 40.0
        # 合并结果
        cmp_res[k] = np.append(partial_sum, last_col_sum)

    # 创建 DataFrame
    df = pd.DataFrame.from_dict(cmp_res, orient="index")
    df.index.name = "Model"
    df.columns = ["action", "action input", "json format", "obs in fa"]

    # 绘制类似矩阵的热力图
    plt.figure(figsize=(10, 6))
    plt.imshow(df, cmap="viridis", aspect="auto")
    plt.colorbar(label="Value")

    # 设置坐标轴标签和刻度
    plt.xticks(np.arange(len(df.columns)), df.columns)
    plt.yticks(np.arange(len(df.index)), df.index)

    # 添加数值注释，将数值转换为百分比形式
    for i in range(len(df.index)):
        for j in range(len(df.columns)):
            plt.text(j, i, f"{df.iloc[i, j]:.2%}", ha="center", va="center", color="w")

    plt.title("Comparison Results: Error Rates")
    plt.xlabel("Metrics")
    plt.ylabel("Model")
    plt.tight_layout()

    # 显示图形
    plt.savefig("../../assets/compare_res.png")
    plt.show()
