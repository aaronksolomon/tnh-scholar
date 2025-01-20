import click

from tnh_scholar.text_processing import normalize_newlines


@click.command()
@click.argument("input_file", type=click.File("r"), default="-")
@click.option(
    "-o",
    "--output",
    type=click.File("w"),
    default="-",
    help="Output file (default: stdout)",
)
@click.option(
    "-s", "--spacing", default=2, help="Number of newlines between blocks (default: 2)"
)
def nfmt(input_file, output, spacing):
    """Normalize the number of newlines in a text file."""
    text = input_file.read()
    result = normalize_newlines(text, spacing)
    output.write(result)


def main():
    """Entry point for the nfmt CLI tool."""
    nfmt()


if __name__ == "__main__":
    main()
