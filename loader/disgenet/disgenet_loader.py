from loader.util import write_batches, get_file, read_tsv


def load_disgenet(session, max_diseases, num_jobs, batch_size):
    if max_diseases is None or max_diseases > 0:
        print("  ")
        print("Opening Disgenet dataset...")
        print("  ")
        insert_associations(session, max_diseases, num_jobs, batch_size)
        print(".....")
        print("Finished migrating Disgenet.")
        print(".....")


def insert_associations(session, max_rows, num_jobs, batch_size):
    get_file("https://www.disgenet.org/static/disgenet_ap1/files/downloads/all_gene_disease_associations.tsv.gz", "dataset/disgenet")
    rows = read_tsv("dataset/disgenet/all_gene_disease_associations.tsv.gz", archive="gz")
    dataset = list()

    for row in rows[:max_rows]:
        data = {
            "entrez-id": row[0].strip(),
            "gene-symbol": row[1].strip(),
            "disease-id": row[4].strip(),
            "disease-name": row[5].strip(),
            "disgenet-score": row[9].strip()
        }

        dataset.append(data)

    insert_diseases(dataset, session, num_jobs, batch_size)
    queries = list()
    print("  Starting with gene disease associations.")

    for data in dataset:
        query = " ".join([
            "match",
            "$g isa gene, has gene-symbol \"{}\";",
            "$d isa disease, has disease-id \"{}\";",
            "not {{ (associated-gene: $g, associated-disease: $d) isa gene-disease-association; }};",
            "insert",
            "(associated-gene: $g, associated-disease: $d) isa gene-disease-association, has disgenet-score {};",
        ]).format(
            data['gene-symbol'],
            data['disease-id'],
            data['disgenet-score'],
        )

        queries.append(query)

    write_batches(session, queries, num_jobs, batch_size)
    print(" gene-disease associations inserted! ({} entries)".format(len(queries)))


def insert_diseases(dataset, session, num_jobs, batch_size):
    print("  Starting with diseases.")
    diseases = dict()
    queries = list()

    for data in dataset:
        if data["disease-id"] != "":
            if data["disease-id"] not in diseases:
                diseases[data["disease-id"]] = set()

            if data["disease-name"] != "":
                diseases[data["disease-id"]].add(data["disease-name"])

    for disease_id in diseases.keys():
        query = "insert $d isa disease, has disease-id \"{}\"".format(disease_id)

        for name in diseases[disease_id]:
            query += ", has disease-name \"{}\"".format(name)

        query += ";"
        queries.append(query)

    write_batches(session, queries, num_jobs, batch_size)
    print(" Diseases inserted! ({} entries)".format(len(diseases)))