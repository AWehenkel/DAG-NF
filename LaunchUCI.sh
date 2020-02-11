#!/usr/bin/env bash
sbatch UCIExperiments.sh power 5000 500 50 .1 150,150,150,150 100,100,30
sbatch UMNN_MAF_UCIExperiments.sh power 5000 500 150,150,150,150 100,100,30

sbatch UCIExperiments.sh gas 5000 500 50 .1 200,200,200 100,100,30
sbatch UMNN_MAF_UCIExperiments.sh gas 5000 500 200,200,200 100,100,30

sbatch UCIExperiments.sh hepmass 100 500 50 .1 200,200,200,200 512,512,30
sbatch UMNN_MAF_UCIExperiments.sh hepmass 100 500 200,200,200,200 512,512,30

sbatch UCIExperiments.sh miniboone 500 500 50 .1 50,50,50 512,30
sbatch UMNN_MAF_UCIExperiments.sh miniboone 500 500 50,50,50 512,30

sbatch UCIExperiments.sh bsds300 100 500 50 .1 150,150,150,150 1024,1024,30
sbatch UMNN_MAF_UCIExperiments.sh bsds300 100 500 150,150,150,150 1024,1024,30