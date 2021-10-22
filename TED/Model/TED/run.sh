#!/bin/bash

dataset="T20H"
folder="data/${dataset}/"
node_file="${folder}node.dat"
config_file="${folder}config.dat"
link_file="${folder}link.dat"
label_file="${folder}label.dat"
emb_file="${folder}emb.dat"

rpt="PCC,PCCC,PCIC,PCPC,PCPCC"
meta="0,2,3,4" # Choose the meta-paths used for training. Suppose the targeting node type is 1 and link type 1 is between node type 0 and 1, then meta="1" means that we use meta-paths "101".
size=50
nhead="8"
dropout=0.4
neigh_por=0.6
lr=0.005
weight_decay=0.0005
batch_size=256
epochs=300
device="cuda"

attributed="True"
supervised="True"


for ratio in '5v5' '4v6' '3v7' '2v8' '1v9'
do
if [ "${dataset}" = "T15S" ] || [ "${dataset}" = "T20H" ]
then
    label_file="${folder}label_TaxPayer${ratio}.dat"
else
    label_file="label.dat"
fi

python3 src/main.py --node=${node_file} --link=${link_file} --config=${config_file} --label=${label_file} --output=${emb_file} --device=${device} --meta=${meta} --size=${size} --nhead=${nhead} --dropout=${dropout} --neigh-por=${neigh_por} --lr=${lr} --weight-decay=${weight_decay} --batch-size=${batch_size} --epochs=${epochs} --ratio=${ratio} --attributed=${attributed} --supervised=${supervised}

name="${folder}/"
if [ "${attributed}" = "True" ]
then
    name="${name}Att"
else
    name="${name}UnAtt"
fi
if [ "${supervised}" = "True" ]
then
    if [ "${dataset}" = "T20H" ] || [ "${dataset}" = "T15S" ]
    then
        name="${name}_Sup_${ratio}.emb.dat"
    else
        name="${name}_UnSup_${ratio}.emb.dat"
    fi
else
    name="${name}_UnSup.emb.dat"
fi
cp "${emb_file}" "${name}"
done
