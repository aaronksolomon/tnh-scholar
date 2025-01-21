# setup.py
from setuptools import setup
from setuptools.command.install import install

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        message = r"""
********************************************************************

             🎉 Thanks for Installing TNH-SCHOLAR 🎉

🚀 NEXT STEPS:
1. Run the command: `tnh-setup` to configure your environment.
2. Visit the documentation for guidance and examples:
🔗 https://aaronksolomon.github.io/tnh-scholar/

💡 TIP: If you encounter any issues, check the docs or 
        file an issue on GitHub.
        
REMEMBER: TNH-SCHOLAR is in prototype phase. 
          Please help improve it by using it and reporting issues!

*********************************************************************"""
        print(f"{message}\n")

setup(
    cmdclass={
        'install': PostInstallCommand,
    },
)