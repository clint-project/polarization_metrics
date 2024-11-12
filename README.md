# Misinformation and echo chambers in social media

Code to reproduce the calculations for the polarization, the entropy and flow diversity and the chamber overlap as done in "A cross-platform analysis of polarization and echo chambers in climate change discussions" by Aleix Bassolas , Joan Massachs, Emanuele Cozzo, and Julian Vicens.
https://arxiv.org/abs/2410.21187


## Requirements

The requirements to run the scripts are detailed in requirements_misinformation.txt

## Code explanation

All the three scripts can be run by typing sh run_scripts.sh

### Network polarization

By running polarization.py you can calculate the polarization metrics: modularity and E-I indices in the real and randomized cases.
Run it with the command python3 polarization.py network_file

### Entropy and polarization

By running entropy.py you can quantify the entropy of flows for each community and their isolation in terms of the ration of external flow vs internal flow.
The script need as input a networkx object file with the graph and a json with the community assignment for nodes.
The input variables are provided in a json configuration file with the following fields:

path: path to the input files required
network_file: name of the file with the networkx object in .gml
community_file: name of the file where the communities of each user are stored in a dictionary structure

### Chamber overlap

By running chamber_analysis.py you can quantify the chamber overlap between the top XX users with higher inflow.
The algorithm is centered in the two communities that we took as the two largest communities with opposed political bias.
The input parameters are provided in a json configuration file and include the fields:

path: path to the input files required
network_file: name of the file with the networkx object in .gml
community_file: name of the file where the communities of each user are stored in a dictionary structure
relevant_communities: list of communities to be considered in the chamber overlap
n_top_users: number of top users to be included in the analysis (this variable has a strong impact in the performance of the algorithm)

An example of a config file is available at config_chamber.josn

Run the script as python3 chamber_overlap.py config_chamber.json

## Contact

If you have any questions, please contact the corresponding author Aleix Bassolas
https://doi.org/10.5281/zenodo.14095108
