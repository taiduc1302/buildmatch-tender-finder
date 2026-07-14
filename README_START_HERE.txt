TENDER_FINDER - SIMPLE START GUIDE
=========================

This file is for a normal user.
You can open it in Notepad.


WHAT THIS FOLDER IS
-------------------

This folder contains the TENDER_FINDER program.
TENDER_FINDER helps build an Excel file with tenders and project leads.


WHAT TO DO FIRST
----------------

1. Open this folder.
2. Double-click:

   setup_venv.bat

3. Wait for setup to finish.
   This may take a few minutes.


HOW TO CHECK THAT IT IS READY
-----------------------------

Double-click:

   verify_package.bat

If the last line says:

   VERIFY_PACKAGE: PASS

then TENDER_FINDER is ready to use.


HOW TO OPEN TENDER_FINDER
----------------

Double-click:

   Launch_TENDER_FINDER_GUI.bat

The TENDER_FINDER window will open.


WHAT TO CLICK IN THE TENDER_FINDER WINDOW
--------------------------------

If you have tender email alerts saved as .eml files:

1. Click:
   Create / Open Email Import Folder

   This opens the folder where TENDER_FINDER reads email files.

2. Copy your .eml files into that folder.

3. Go back to the TENDER_FINDER window and click:
   Test Email Import

   This checks that TENDER_FINDER can read the email files.

4. If that looks good, click:
   Run Demo With Email Alerts

   This is the main run with email alert input.


IF YOU DO NOT HAVE .EML FILES
-----------------------------

You can still run TENDER_FINDER.

For a faster run, double-click:

   run_tenderfinder_demo_fast.bat

For a fuller run, double-click:

   run_tenderfinder_demo.bat


FAST VS FULL
------------

run_tenderfinder_demo_fast.bat
- Faster
- Good for a quick check

run_tenderfinder_demo.bat
- Slower
- Runs a more complete sweep


WHERE TO FIND THE RESULT
------------------------

After a successful run, TENDER_FINDER usually creates output here:

   C:\tenderfinder_out\demo_p522\

Main result file:

   TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx

You may also want to open:

   DEMO_BUILD_REPORT.md
   demo_summary.txt
   DEMO_TALKTRACK.md


IF SOMETHING DOES NOT WORK
--------------------------

1. Run:
   verify_package.bat

2. Make sure you already ran:
   setup_venv.bat

3. If the TENDER_FINDER window does not open, try:
   run_tenderfinder_demo_fast.bat


QUICK ORDER
-----------

1. setup_venv.bat
2. verify_package.bat
3. Launch_TENDER_FINDER_GUI.bat
4. Click Create / Open Email Import Folder
5. Put .eml files into that folder
6. Click Test Email Import
7. Click Run Demo With Email Alerts

