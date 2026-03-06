import io
import pathlib
import pandas as pd



def dataframe_schema_info(df: pd.DataFrame) -> str:
    buffer = io.StringIO()
    df.info(buf=buffer, show_counts=False)
    info_str = buffer.getvalue()

    # Convert the info string to a markdown table
    lines = info_str.splitlines()
    header = "| # | Column | Dtype |"
    separator = "|--------|----------------|-------|"
    table = [header, separator]

    for line in lines[5:-2]:  # Skip useless lines
        parts = line.split()
        if len(parts) >= 3:
            column = parts[0]
            non_null_count = parts[1]
            dtype = parts[2]
            table.append(f"| {column} | {non_null_count} | {dtype} |")

    markdown_table = "\n".join(table)
    return markdown_table


if __name__ == "__main__":
    curr_path = pathlib.Path(__file__)
    data_folder_path = curr_path.parent.parent / "data/samples"
    output_md_file = curr_path.parent.parent / "docs/dataframes_schema.md"

    dataframes = {
        "inb_df": "Inbound / Outbound flight data",
        "merged_df_orig": "Merged inbound and outbound flight data",
        "price_graph_df": "Gantt chart data",
        "heatmap_df": "Heatmap chart data",
        "flight durations binned": "Flight duration binned data",
    }

    with open(output_md_file, "w") as f:
        f.write("## Dataframes Schema\n\n")
        f.write("Documentation automatically generated from [`scripts/generate_dataframe_schemas.py`](/scripts/generate_dataframe_schemas.py)\n\n")

        for df_name, title in dataframes.items():
            df: pd.DataFrame = pd.read_pickle(data_folder_path / f"{df_name}.pkl")

            f.write(f"### {title}\n")
            info_str = dataframe_schema_info(df)
            f.write(info_str + "\n\n")
            f.write("#### Sample Data\n")
            sample_markdown = df.head(5).to_markdown()
            f.write(sample_markdown + "\n\n")
            f.write("---\n\n")
