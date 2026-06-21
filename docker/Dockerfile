# 1. Partiamo dall'immagine base
FROM cogar_base

# 2. Imposta le variabili d'ambiente
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "export IGN_GAZEBO_RESOURCE_PATH=\$IGN_GAZEBO_RESOURCE_PATH:/workspace/src/aws-robomaker-small-house-world/models" >> /root/.bashrc

# 3. Imposta la cartella di lavoro
WORKDIR /workspace

# Nessun ENTRYPOINT verso script esterni
CMD ["bash"]
