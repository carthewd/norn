# norn
`norn` is a tool to aide in building and testing with CloudWatch Events. It provides a list of sample events for all services published in the AWS documentation (it does this by retrieving the docs from the `awsdocs` GitHub repositories).

In addition, it provides some basic functionality to replace common fields (e.g., region, accounts) for the sample events. You can use this to simply generate JSON dumps of the events and incorporate them into tests or execute Python-based Lambda functions with the selected event as an input. 

This is still in the very early stages of development 

## Usage 

- `norn services`
- `norn events -s <service_name>`
- `norn trigger -e <service_name.N> -n <lambda_function_name>`

## Installation

For now, there's a prebuilt wheel in dist: `pip install https://github.com/carthewd/norn/blob/master/dist/norn-<version>-py3-none-any.whl`
