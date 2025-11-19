import click

from tnh_scholar.gen_ai_service.utils.token_utils import token_count


@click.command()
@click.argument("input_file", type=click.File("r"), default="-")
def token_count_cli(input_file):
    """Return the Open AI API token count of a text file. Based on gpt-4o."""
    text = input_file.read()
    result = token_count(text)
    click.echo(result)


def main():
    """Entry point for the token-count CLI tool."""
    token_count_cli()


if __name__ == "__main__":
    main()
