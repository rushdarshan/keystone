import timm
import torch


def load_dinov3(model_name: str = "vit_base_patch16_reg8_dino",
                device: str = "cuda",
                pretrained: bool = True) -> torch.nn.Module:
    model = timm.create_model(model_name, pretrained=pretrained)
    model = model.eval().to(device)
    return model


def load_fallback(model_name: str = "vit_base_patch14_dinov2",
                  device: str = "cuda",
                  pretrained: bool = True) -> torch.nn.Module:
    print(f"  [model] falling back to {model_name}")
    return load_dinov3(model_name, device, pretrained)
