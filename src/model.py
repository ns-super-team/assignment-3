import torch
from torch import nn
from torchvision.models import vgg19
from torchinfo import summary

from adain import AdaIN


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        # TODO: 
        # [x] pozriet ci tu nie su tie avg.pool, flatten - mali by byt len features
        # self.encoder = list(vgg19(pretrained=True).children())[0][:21] 
        # self.encoder = nn.Sequential(*list(vgg19(weights='VGG19_Weights.DEFAULT').features)[:21])
        self.encoder = nn.Sequential(*list(vgg19(pretrained=True).features)[:21])

        for param in self.encoder.parameters():
            param.requires_grad = False
        
        # create dict for saving activations used in the style loss
        self.activations = {}
        for i, module in enumerate(self.encoder.children()):
            if i in [1, 6, 11, 20]:
                module.register_forward_hook(self._save_activations(i))
        
        self.AdaIN = AdaIN()
        
        # TODO: 
        # [x] zmensit model
        # [x] malo by to byt ako up, conv, relu
        # [x] dat na koniec Tanh
        self.decoder = nn.Sequential(
            nn.Upsample(scale_factor=2.0, mode='nearest'),
            nn.Conv2d(512, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            nn.ReLU(),

            # nn.Conv2d(256, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            # nn.ReLU(),
            # nn.Conv2d(256, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            # nn.ReLU(),
            nn.Upsample(scale_factor=2.0, mode='nearest'),
            nn.Conv2d(256, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            nn.ReLU(),
            nn.Conv2d(256, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            nn.ReLU(),
            
            nn.Upsample(scale_factor=2.0, mode='nearest'),
            nn.Conv2d(128, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            nn.ReLU(),
            nn.Conv2d(128, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            nn.ReLU(),
            
            nn.Conv2d(64, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            nn.ReLU(),
            nn.Conv2d(64, 3, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), padding_mode='reflect'),
            nn.Tanh()
        )

    # https://stackoverflow.com/a/68854535
    def _save_activations(self, name):
        def hook(module, input, output):
            self.activations[name] = output.detach()
        return hook

    def forward(self, content, style):
        enc_content = self.encoder(content)
        enc_style = self.encoder(style)
        
        self.t = self.AdaIN(enc_content, enc_style)
        out = self.decoder(self.t)

        return out
    

if __name__ == '__main__':
    print(summary(NeuralNetwork()))