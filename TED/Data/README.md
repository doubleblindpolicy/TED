## Data

Now we provide a subgraph of ```T20H```. ```T20H``` and ```T15S``` will be published after desensitization.

The statistics of each dataset are as follows.

**Dataset** | #node types | #nodes | #link types | #links | #attributes | #attributed nodes
--- | --- | --- | --- | --- | --- | --- | --- | ---
**T20H** | 4 | 112,015 | 6 | 198,903 | 300 | ALL
**T15S** | 2 | 132,522 | 2 | 467,273 | 300 | ALL

Each dataset contains:
- 2 data files (```node.dat```, ```link.dat```);
- 5 label files (```label_TaxPayer5v5.dat```, ```label_TaxPayer4v6.dat```, ```label_TaxPayer3v7.dat```, ```label_TaxPayer2v8.dat```, ```label_TaxPayer1v9.dat```);
- 5 evaluation files (```label_TaxPayer5v5.dat.test```, ```label_TaxPayer4v6.dat.test```, ```label_TaxPayer3v7.dat.test```, ```label_TaxPayer2v8.dat.test```, ```label_TaxPayer1v9.dat.test```);
- 1 description files (```info.dat```);
- 1 recording file (```record.dat```).

### node.dat

- In each line, there are 4 elements (```node_id```, ```node_name```, ```node_type```, ```node_attributes```) separated by ```\t```. In ```node_attributes```, attributes are separated by comma (```,```).
- In the subgraph of ```T20H```, ```node_name``` is replaced by ```******```.

### link.dat

- In each line, there are 4 elements (```source_node_id```, ```target_node_id```, ```link_type```, ```link_weight```) separated by ```\t```.
- All links are directed. Each node is connected by at least one link.

### label_TaxPayer*v*.dat

- In each line, there are 4 elements (```node_id```, ```node_name```, ```node_type```, ```node_label```) separated by ```\t```.
- All labeled nodes are of the company node type and each labeled node only has one label.
- To simulate the real tax evasion scenarios where the proportion of tax evasion companies are unknown, we further set 5 control groups, changing the positive samples ratio (PSR) of traning sets as 50\%, 40\%, 30\%, 20\%, and 10\% (i.e., 5:5, 4:6, 3:7, 2:8, 1:9).

### label_TaxPayer*v*.dat.test

- In each line, there are 4 elements (```node_id```, ```node_name```, ```node_type```, ```node_label```) separated by ```\t```.
- All labeled nodes are of the company node type and each labeled node only has one label.
- The ratio of positive samples to negative samples in the test sets is 1:1.

### info.dat

- This file describes the meaning of each node type, link type, and label type in the corresponding dataset.

### record.dat

- In each paragraph, the first line tells the model and evaluation settings, the second line tells the set of training parameters, and the third line tells the evaluation results.