import pandas as pd
from Bio import SeqIO

def format_annotations(annot_value):
     if isinstance(annot_value, str):
          if "\n" in annot_value:
               return "\n```" + annot_value + "\n\n```"
          else:
               return annot_value 
        #   return annot_value.replace("\n", "\n\n") # Need double new line for markdown
     elif isinstance(annot_value, list):
          return "\n" + "\n".join(["* " + format_annotations(av) for av in annot_value])
     else:
          return str(annot_value)


def parse_genbank(genbank_path):
    """
    Load a genbank file into a more convenient DataFrame
    """
    rows = []
    locus_sequences = {}

    locus_data_rows = []

    # Iterate through genbank CDS records and convert them to a more convenient data frame
    with open(genbank_path) as handle:
        for i, record in enumerate(SeqIO.parse(handle, "genbank")):
               locus_sequences[record.id] = record.seq

               formatted_annotations = "\n\n".join([f"**{k}**: {format_annotations(v)}" for k, v in record.annotations.items()])

               if record.id == "<unknown id>":
                    record.id = f"LOCUS_{i+1:04d}"

               locus_data_rows.append(
                    [record.id, record.name, record.description, record.dbxrefs, record.annotations, formatted_annotations, record.seq, len(record.seq)]
               )

               for feature in record.features:
                    feature_type = feature.type
                    locus = record.id
                    start = feature.location.start
                    end = feature.location.end
                    strand = feature.location.strand
                    locus_tag = feature.qualifiers.get("locus_tag", ["no_tag"])[0]
                    product = feature.qualifiers.get("product", ["no_product"])[0]
                    gene = feature.qualifiers.get("gene", ["no_gene_name"])[0]
                    label = feature.qualifiers.get("gene", ["no_label"])[0]

                    qualifiers_list = []
                    for k, value_list in feature.qualifiers.items():
                         for v in value_list:
                              qualifiers_list.append((k,v))

                    qualifiers = "\n".join([f"{k}={v}" for k, v in qualifiers_list])
                    formatted_qualifiers = "\n\n".join([f"**{k}**: {v}" for k, v in qualifiers_list])
                    
                    rows.append([feature_type, locus, int(start), int(end), strand, locus_tag, product, gene, label, qualifiers, formatted_qualifiers])
    
    genbank_features = pd.DataFrame(
        rows, 
        columns=["feature_type", "locus", "start", "end", "strand", "locus_tag", "product", "gene", "label", "qualifiers", "formatted_qualifiers"]
    ).sort_values(["locus", "start"])

    genbank_loci = pd.DataFrame(
        locus_data_rows, 
        columns=["locus_id", "name", "description", "dbxrefs", "annotations", "formatted_annotations", "sequence", "sequence_length"],
    )
    genbank_loci = genbank_loci.set_index("locus_id")

    return genbank_features, genbank_loci
