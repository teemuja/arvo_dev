import pkg_resources

# Path to your requirements.txt file
requirements_file = "requirements.txt"

# Read the requirements file to get the list of required packages
with open(requirements_file, 'r') as file:
    required_packages = [line.strip() for line in file if line.strip() and not line.startswith('#')]

# For each package, print its installed version
for package in required_packages:
    try:
        # Parse out only the package name if there's a version or other specifiers
        package_name = package.split('==')[0].split('>')[0].split('<')[0]
        version = pkg_resources.get_distribution(package_name).version
        print(f"{package_name}: {version}")
    except pkg_resources.DistributionNotFound:
        print(f"{package_name}: Not installed")
