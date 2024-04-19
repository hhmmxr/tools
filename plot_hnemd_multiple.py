import math
import numpy as np
import matplotlib.pyplot as plt
from gpyumd.math import running_ave
from gpyumd.load import load_kappa

kappa = np.loadtxt('kappa.out', max_rows=10000*4)   #下面俩数相乘
num_kappas = 4    #执行几次
lines_per_file = 10000    #一次多少行
file_datas = np.split(kappa, num_kappas)
t = np.arange(1, lines_per_file + 1) * 0.001

plt.figure(figsize=(17, 5))

def plot_running_avg(data, subplot_index, color, ylabel, ylimit, yticks, title_tag):
    ax = plt.subplot(1, 3, subplot_index)
    avg_data = np.zeros_like(data[0])
    for dataset in data:
        plot_data = running_ave(dataset, t)
        plt.plot(t, plot_data, color='C7', alpha=0.5)
        avg_data += plot_data
    avg_data /= num_kappas
    plt.plot(t, avg_data, color=color, linewidth=2)
    plt.annotate(f'{avg_data[-1]:.2f}', xy=(t[-1], avg_data[-1]), xytext=(-20, 5), textcoords='offset points', ha='center', va='bottom')
    
    plt.xlim([0, 10])
    plt.ylim([0, ylimit])
    plt.gca().set_xticks(np.arange(0, 11, 2))
    plt.gca().set_yticks(np.arange(0, ylimit+1, yticks))
    plt.xlabel('time (ns)')
    plt.ylabel(ylabel)
    plt.title(f'({title_tag})')

ki_data = [file_datas[i][:, 2] for i in range(num_kappas)]   #0为xi，2为yi
ko_data = [file_datas[i][:, 3] for i in range(num_kappas)]   #1为xo，3为yo
plot_running_avg(ki_data, 1, 'red', r'$\kappa_{in}$ W/m/K', 1000, 200, 'a')
plot_running_avg(ko_data, 2, 'blue', r'$\kappa_{out}$ W/m/K', 1000, 200, 'b')

plt.subplot(1, 3, 3)
plt.plot(t, running_ave(np.mean(np.array(ki_data), axis=0),t), 'red', label='in', linewidth=2)
plt.plot(t, running_ave(np.mean(np.array(ko_data), axis=0),t), 'blue', label='out', linewidth=2)
running_avg_k = running_ave(np.mean(np.array(ki_data), axis=0) + np.mean(np.array(ko_data), axis=0), t)
plt.plot(t, running_avg_k, 'black', label='total', linewidth=2)
plt.annotate(f'{running_avg_k[-1]:.2f}', xy=(t[-1], running_avg_k[-1]), xytext=(-20, -10), textcoords='offset points', ha='center', va='bottom')
plt.xlim([0, 10])
plt.ylim([0, 2000])
plt.gca().set_xticks(np.arange(0, 11, 2))
plt.gca().set_yticks(np.arange(0, 2001, 400))
plt.xlabel('time (ns)')
plt.ylabel(r'$\kappa_{total}$ W/m/K')
plt.title('(c)')
plt.legend(['in', 'out', 'total'])

plt.savefig('hnemd.png', dpi=150, bbox_inches='tight')

plt.figure(figsize=(6, 5))
kz_data = [file_datas[i][:, 4] for i in range(num_kappas)]
plt.plot(t, running_ave(np.mean(np.array(kz_data), axis=0),t), 'black', linewidth=2)
plt.xlim([0, 10])
plt.ylim([0, 500])
plt.gca().set_xticks(np.arange(0, 11, 2))
plt.gca().set_yticks(np.arange(0, 501, 100))
plt.xlabel('time (ns)')
plt.ylabel(r'$\kappa_{z}$ (W/m/K)')

plt.savefig('hnemd-z.png', dpi=150, bbox_inches='tight')

