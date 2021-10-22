#!/bin/bash

dataset='T20H'
model='TED'
attributed='True'
supervised='True'


for r in  '5v5'
do
python evaluate.py -dataset ${dataset} -model ${model} -attributed ${attributed} -supervised ${supervised} -ratio ${r}
done


