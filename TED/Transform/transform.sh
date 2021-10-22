#!/bin/bash

dataset='T20H'
model='TED' 
attributed='True' 
supervised='True'

mkdir ../Model/${model}/data
mkdir ../Model/${model}/data/${dataset}

python transform.py -dataset ${dataset} -model ${model} -attributed ${attributed} -supervised ${supervised}