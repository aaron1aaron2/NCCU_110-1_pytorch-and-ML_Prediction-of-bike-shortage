# 本專案是使用 conda 建立環境，也可以用 pyenv 或 virtualenv 建立環境。(建議使用python3.7)
conda create --name ml_pytorch_class python=3.7
conda activate ml_pytorch_class 

# Dependency package
pip install -r requirements.txt

# Pytorch (請到 https://pytorch.org/ 選擇適合的版本)
conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch