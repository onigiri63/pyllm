@echo off
setlocal

:: Prompt user for container name or ID
set /p CONTAINER_ID=Enter the container ID or name: 

:: Prompt user for the output filename (without extension)
set /p FILENAME=Enter output tar filename (without .tar): 

:: Set image tag equal to the filename
set IMAGE_TAG=%FILENAME%

:: Commit the container to a new image
docker commit %CONTAINER_ID% %IMAGE_TAG%
if errorlevel 1 (
    echo Failed to commit container. Exiting.
    exit /b 1
)

:: Save the image as a tar file
docker save -o %FILENAME%.tar %IMAGE_TAG%
if errorlevel 1 (
    echo Failed to save image. Exiting.
    exit /b 1
)

echo Image saved to %FILENAME%.tar successfully.

endlocal
pause
