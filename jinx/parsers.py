import pandas as pd
from Bio import SeqIO

def parse_genbank(genbank_path):
    """
    Load a genbank file into a more convenient DataFrame
    """
    rows = []
    locus_sequences = {}

    # Iterate through genbank CDS records and convert them to a more convenient data frame
    with open(genbank_path) as handle:
        for record in SeqIO.parse(handle, "genbank"):
            locus_sequences[record.id] = record.seq

            for feature in record.features:
                    feature_type = feature.type
                    locus = record.id
                    start = feature.location.start
                    end = feature.location.end
                    strand = feature.location.strand
                    locus_tag = feature.qualifiers.get("locus_tag", ["no_tag"])[0]
                    product = feature.qualifiers.get("product", ["no_product"])[0]
                    gene = feature.qualifiers.get("gene", ["no_gene_name"])[0]
                    
                    rows.append([feature_type, locus, int(start), int(end), strand, locus_tag, product, gene])
    
    genbank_features = pd.DataFrame(
        rows, 
        columns=["feature_type", "locus", "start", "end", "strand", "locus_tag", "product", "gene"]
    ).sort_values(["locus", "start"])

    return genbank_features, locus_sequences
