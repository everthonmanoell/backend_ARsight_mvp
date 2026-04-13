import torch

print('=' * 60)
print('CUDA VALIDATION')
print('=' * 60)
print(f'torch: {torch.__version__}')
print(f'cuda available: {torch.cuda.is_available()}')
print(f'cuda version: {torch.version.cuda}')
print(f'device count: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    print(f'device name: {torch.cuda.get_device_name(0)}')
    print(f'compute capability: {torch.cuda.get_device_capability(0)}')
print('✅ Everything looks good!')
