import datetime
import torch 
import os 

from torch.nn.functional import one_hot

from .data_loader import filename_to_tensor 
from .accuracy import accuracy

def training_loop(n_epochs, optimizer, model, loss_fn, train_loader, val_loader, transform, saved_path, eval_interval=5):
    '''
    Parameters:
        n_epochs (int): Number of epoch trained
        optimizer (torch.optim): Optimizer
        model (nn.Module): training model
        loss_fn (torch.nn.modules.loss): Loss function
        train_loader (dict): Custom training data loader in utils/dataloader.py {'img_path': [...], 'label': [...]}
        val_loader (dict): Custom validate data loader in utils/dataloader.py {'img_path': [...], 'label': [...]}
        transform (torchvision.transforms.transforms): requires to transform to Tensor after augment
        saved_path (os.path or str): dir to save weight checkpoint
        
        eval_interval (int): validate after a number of epochs
    '''
    min_loss = 10000
    for epoch in range(1, n_epochs + 1):  
        loss_train = 0.0
        
        # For each batch
        for i in range(len(train_loader['label'])):
            # Read data from data loader and transform filename into tensor
            filenames = train_loader['img_path'][i]
            labels = train_loader['label'][i]
            img_batch = filename_to_tensor(filenames, transform)
            
            # Use ViT for prediction
            outputs = model(img_batch)
            
            # Convert label to one-hot format to calculate loss
            num_classes= train_loader['num_classes']
            actual = one_hot(labels, num_classes).type(torch.float32)
            loss = loss_fn(outputs, actual)
            
            # Backpropagation
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Sum all loss to calculate the loss of the epoch
            loss_train += loss.item()
        
        # Average loss over batches
        avg_loss = loss_train / len(train_loader['label'])
        
        
        # Replace best checkpoint if loss < min_loss:
        if avg_loss < min_loss:
            min_loss = avg_loss
            torch.save(model.state_dict(), os.path.join(saved_path, "best_ckpt.pt"))
        
        
        # Print loss of epoch
        print(f"{datetime.datetime.now()} Epoch {epoch}, Training loss {avg_loss}")

        # Eval interval
        # After a number of epoch, evaluate
        if epoch == 1 or epoch % eval_interval == 0:
            loss_val = 0.0
            with torch.no_grad():
                for k in range(len(val_loader['label'])):
                    # Read data from data loader and transform filename into tensor
                    val_filenames = val_loader['img_path'][k]
                    val_labels = val_loader['label'][k]
                    val_img_batch = filename_to_tensor(val_filenames, transform)
                    
                    # Use ViT for prediction, then calculate the loss 
                    val_outputs = model(val_img_batch)
                    batch_loss_val = loss_fn(val_outputs, val_labels)
                    
                    # Sum all loss to calculate the loss of the epoch
                    loss_val += batch_loss_val.item()
                
            # Print validation loss
            print(f"{datetime.datetime.now()} Epoch {epoch}, Validation loss {loss_val / len(val_loader)}")
            accuracy(model, val_loader, transform)
            print("-"*20)
            print("")
            
        
    # Save last checkpoint
    torch.save(model.state_dict(), os.path.join(saved_path, "last_ckpt.pt"))
        