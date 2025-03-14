克隆GPT-SoVITS项目，下载基础模型和训练好的模型并放入指定文件夹下

切到commit id b7a904a67153170d334fdc0d7fbae220ee21f0e9

新建my_infer.yaml


my_infer.yaml：要修改的是t2s_weights_path（放GPT权重）和vits_weights_path（放SoVITS权重）

```yaml
custom:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cuda
  is_half: true
  t2s_weights_path: /home/pika/Repo/GPT-SoVITS/GPT_weights_v2/xxx-e15.ckpt
  version: v2
  vits_weights_path: /home/pika/Repo/GPT-SoVITS/SoVITS_weights_v2/xxx_e4_s44.pth
default:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
  version: v1
  vits_weights_path: GPT_SoVITS/pretrained_models/s2G488k.pth
default_v2:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt
  version: v2
  vits_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth
```

```ps
cd ~/Repo/GPT-SoVITS/
python api_v2.py -a 127.0.0.1 -p 9880 -c  GPT_SoVITS/configs/my_infer.yaml
```

这里的api_v2.py是指原仓库里的，如果报错，再按照本README目录下的api_v2.py进行相应修改。

