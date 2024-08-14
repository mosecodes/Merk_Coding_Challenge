# Merk Coding Challenge

This project is a submission for a major coding challenge posted by Merck for a Software Engineer position. The challenge was two-fold: first, use their open source project <code>Pyplate</code> to build a chemistry experiment involving 96-well plates and testing various reagents with a Palladium catalyst in different solvents; second, use their other open source project <code>rainbow</code> to interpret sample binary files which imitated the proprietary binary file formats of different mass spectrometry and chemical analysis intstruments. These challenges required significant effort so I wanted to document my submission now that the challenge period is over. My submission was turned down, but was praised for technical accuracy and solid design principles. 

This submission is divided into two sections, corresponding to the sections of the challenge. To get started evaluating, simply download and extract the zip or clone the repository (I recommend PyCharm, but it should work in any IDE that runs Python) and navigate to each section for grading and running the scripts. You may need to install the packages I used, including Numpy, pandas, and the pyplate & rainbow packages. I didn't need to do this in PyCharm, but in VSCode I ran into issues just running it straight from cloning it and straight from the zip. Below is the information you need to evaluate each section.

### Section 1 - PyPlate Notebook
For best results, open a terminal in the Section 1 folder and run the <code>jupyter notebook</code> command. If you aren't wanting to run the notebook in a jupyter server, the Merk_Coding_Challenge.ipynb file should still render in your IDE (you may need to install plugins, but in PyCharm it worked fine). If rendering in your IDE, the output for the code cell will render the generated tables after all of the text output instead of incorporating them as intended, but if that's fine then you don't need to spin up a jupyter server.

### Section 2 - Rainbow Scripts
The cloned repository will come with the csv_files folders already present for evaluation. If you want to regenerate them using the scripts, you will have to delete them in your own project and then run the scripts. They are in separate folders and have the names X_main.py, where X is one of [pear, scale, sixtysix]. 

_Note: The project folder for this section is actually in Merck_Coding_Challenge>Section 2>PythonProject, whereas for section 1 is just Merck_Coding_Challenge>Section 1_
