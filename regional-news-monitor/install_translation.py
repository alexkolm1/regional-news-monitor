from argostranslate import package

if not any(item.from_code == "fr" and item.to_code == "en"
           for item in package.get_installed_packages()):
    package.update_package_index()
    model = next(item for item in package.get_available_packages()
                 if item.from_code == "fr" and item.to_code == "en")
    package.install_from_path(model.download())
