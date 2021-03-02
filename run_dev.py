import torch
import sys
from src_dev.LRP import LRP
from src_dev.util import model_io,load_from,write_to
import yaml
from src_dev.model.GraphDataset import GraphDataset
from src_dev.model.InteractionNetwork import InteractionNetwork
from tqdm import tqdm
from torch_geometric.data import DataLoader


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


if __name__=="__main__":
    # get the targets
    targets=sys.argv[1:]
   
    # load feature definitions
    with open('./data/definitions.yml') as file:
        definitions = yaml.load(file, Loader=yaml.FullLoader)
    
    features = definitions['features']
    spectators = definitions['spectators']
    labels = definitions['labels']

    nfeatures = definitions['nfeatures']
    nspectators = definitions['nspectators']
    nlabels = definitions['nlabels']
    ntracks = definitions['ntracks']


    if "test" in targets:                     # run targets on dev data
        file_names=["./test/test.root"]
    else:                                     # run targets on actual data
        file_names=["/teams/DSC180A_FA20_A00/b06particlephysics/train/ntuple_merged_0.root"]
    
    # start a model
    model=InteractionNetwork().to(device)
    

    # run targets related to actual usage of the project with trained model
    if not (("sanity-check" in targets) or ("sc" in targets)):  
        graph_dataset = GraphDataset('./data', features, labels, spectators, n_events=10000, n_events_merge=1000, 
                                    file_names=file_names)
        
        batch=graph_dataset[0]
        batch_size=1
        batch_loader=DataLoader(batch,batch_size = batch_size)

        if "explain" in targets:    
            state_dict=torch.load("./data/model/IN_best_dec10.pth",map_location=device)
            model=model_io(model,state_dict,dict())

            t=tqdm(enumerate(batch_loader),total=len(batch)//batch_size)
            explainer=LRP(model)
            results=[]

            if "QCD" in targets:   # relevance w.r.t. QCD
                signal=torch.tensor([1,0],dtype=torch.float32).to(device)
                save_to="./data/file_0_relevance_QCD.pt"
            else:                  # default: relevance w.r.t. Hbb
                signal=torch.tensor([0,1],dtype=torch.float32).to(device)
                save_to="./data/file_0_relevance.pt"

            for i,data in t:
                data=data.to(device)
                to_explain={"A":dict(),"inputs":dict(x=data.x,
                                                    edge_index=data.edge_index,
                                                    batch=data.batch),"y":data.y,"R":dict()}
                
                model.set_dest(to_explain["A"])
                
                results.append(explainer.explain(to_explain,save=False,return_result=True,
                signal=signal))
                
            torch.save(results,save_to)
        
        if "plot" in targets:       # plot precomputed relevance scores
            pass #todo

    else: # run targets related to sanity check of the explanation method
        if "all" in targets:
            tagets+=["data","train","explain","plot"]
        if "data" in targets:        # generate new data for sanity check purpose
            # declare variables
            nfeatures=48
            ntracks=10
            nsamples=2000+500
            x_idx=0
            y_idx=3
            save_to="./data/{}_sythesized.pt"
            make_data(nfeatures,ntracks,nsamples,x_idx,y_idx,save_to)

        if "train" in targets:       # train on generated train data
            train_data=torch.load("./data/{}_sythesized.pt".format("train"))
            test_data=torch.load("./data/{}_sythesized.pt".format("test"))

            main(train_data,test_data,"./data/model/IN_sythesized.pth","./data/IN_sytehsized_roc.png")

        if "explain" in targets:     # explain the prediction on generated test data
            pass # todo

        if "plot" in targets:        # plot the precomptued relevance score of generated test data
            pass # todo