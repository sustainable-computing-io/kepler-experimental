
1. Create python virtual environment, and activate it
   ```
   python -m venv venv
   source venv/bin/activate
   ```
2. Install jupyter
   ```
   python -m pip install jupyter
   ```
3. install new ipython kernel
   ```
   python -m ipykernel install --name=my-power-model --prefix=$VIRTUAL_ENV
   
   jupyter kernelspec list
   Available kernels:
      my-power-model    /home/vimalkum/src/powermon/kepler-experimental/vimal/venv/share/jupyter/kernels/my-power-model
      python3           /home/vimalkum/src/powermon/kepler-experimental/vimal/venv/share/jupyter/kernels/python3
      jupyter           /home/vimalkum/.local/share/jupyter/kernels/jupyter
   ```
4. Install dependencies
   ```
   pip install scikit-learn
   pip install pandas
   pip install prometheus_api_client
   pip install xgboost
   ```
5. Launch jupyter notebook
   ```
   jupyter lab
   ```
   From the jupyter notebook webpage, use the kernel created above
