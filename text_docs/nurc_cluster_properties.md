# Cluster properties

## QOS Job Limits (gpu partition)

| Limit | Value | Meaning |
|-------|-------|---------|
| MaxSubmitPU | 8 | Max 8 jobs submitted (running + pending) at once |
| MaxJobsPU | 4 | Max 4 jobs actually running concurrently |
| MaxTime | 8:00:00 | Max 8 hours per job |
| DefaultTime | 4:00:00 | Default wall time if not specified |

**Implication:** With 1 master job, max `parallel_jobs = 7` (master + 7 workers = 8 submitted).
Only 4 workers run at a time; the rest wait in queue.
1. sinfo -o "%20P %5a %10l %6D %10s %25f %20G" | head -40
PARTITION            AVAIL TIMELIMIT  NODES  JOB_SIZE   AVAIL_FEATURES            GRES                
gpu                  up    8:00:00    9      1-infinite (null)                    gpu:v100-sxm2:4(S:0-
gpu                  up    8:00:00    2      1-infinite ib,skylake_avx512,prod    gpu:v100-sxm2:4(S:0-
gpu                  up    8:00:00    1      1-infinite ib,cascadelake,prod       gpu:t4:4(S:0-1)     
gpu                  up    8:00:00    1      1-infinite ib,zen2,prod              gpu:a100:3          
gpu                  up    8:00:00    2      1-infinite zen2,prod,ib,a100@80g     gpu:a100:4          
gpu                  up    8:00:00    4      1-infinite cascadelake,prod          gpu:h200:8          
gpu                  up    8:00:00    4      1-infinite zen,prod                  gpu:v100-pcie:2(S:0-
gpu                  up    8:00:00    1      1-infinite (null)                    gpu:v100-sxm2:3(S:0-
gpu                  up    8:00:00    1      1-infinite (null)                    (null)              
short*               up    2-00:00:00 24     1-2        ib,cascadelake,prod       (null)              
short*               up    2-00:00:00 296    1-2        (null)                    (null)              
short*               up    2-00:00:00 1      1-2        ib,skylake_avx512,prod    gpu:v100-sxm2:4(S:0-
sharing              up    1:00:00    51     1-2        broadwell,prod            (null)              
sharing              up    1:00:00    27     1-2        ib,cascadelake,prod       (null)              
sharing              up    1:00:00    2      1-2        zen2,prod,rocm            gpu:mi50:8          
sharing              up    1:00:00    368    1-2        (null)                    (null)              
sharing              up    1:00:00    2      1-2        ib,skylake_avx512,prod    gpu:v100-sxm2:4(S:0-
sharing              up    1:00:00    2      1-2        ib,lotterhos,skylake_avx5 (null)              
sharing              up    1:00:00    1      1-2        ib,cascadelake,prod       gpu:quadro:3        
sharing              up    1:00:00    1      1-2        zen2,prod,rocm            (null)              
sharing              up    1:00:00    1      1-2        haswell,prod              (null)              
sharing              up    1:00:00    1      1-2        ivybridge,prod            (null)              
sharing              up    1:00:00    1      1-2        (null)                    gpu:quadro:3        
sharing              up    1:00:00    7      1-2        ib,cascadelake,prod       gpu:v100:4          
sharing              up    1:00:00    1      1-2        ib,cascadelake,prod8      gpu:v100:4          
sharing              up    1:00:00    3      1-2        zen2,prod,dgx             gpu:a100:8          
sharing              up    1:00:00    1      1-2        zen2,prod,dgx             gpu:a100:7          
sharing              up    1:00:00    1      1-2        zen2,prod                 gpu:a6000:8         
sharing              up    1:00:00    1      1-2        (null)                    gpu:a5000:8         
sharing              up    1:00:00    1      1-2        prod,ib                   gpu:a100:8          
sharing              up    1:00:00    1      1-2        cascadelake,prod,ib       gpu:a100:8          
sharing              up    1:00:00    12     1-2        zen2,prod,ib              (null)              
sharing              up    1:00:00    2      1-2        cascadelake,prod,ib       gpu:l40:10          
sharing              up    1:00:00    1      1-2        (null)                    gpu:a6000:8         
sharing              up    1:00:00    1      1-2        ib,cascadelake,prod       gpu:h100:4          
sharing              up    1:00:00    2      1-2        ib,zen2,prod              gpu:l40s:8          
sharing              up    1:00:00    1      1-2        ib,xen2,prod              gpu:l40s:8          
sharing              up    1:00:00    5      1-2        prod                      gpu:l40s:4          
sharing              up    1:00:00    1      1-2        skylake_avx512,prod       gpu:v100-sxm2:4(S:0-

2. sinfo -o "%20N %10P %10G %6c %10m %25f" --Node | grep -i gpu | head -30
c2184                sharing    gpu:p100:3 28     512000     broadwell,prod           
c2185                sharing    gpu:p100:4 28     512000     broadwell,prod           
c2186                sharing    gpu:p100:4 28     512000     broadwell,prod           
c2187                sharing    gpu:p100:4 28     512000     broadwell,prod           
c2188                sharing    gpu:p100:3 28     512000     broadwell,prod           
c2193                sharing    gpu:p100:4 28     512000     broadwell,prod           
c2194                sharing    gpu:p100:4 28     512000     broadwell,prod           
c2195                sharing    gpu:p100:4 28     512000     broadwell,prod           
c2204                gpu-intera gpu:v100-p 32     480000     zen,prod                 
c2204                gpu-short  gpu:v100-p 32     480000     zen,prod                 
c2204                gpu        gpu:v100-p 32     480000     zen,prod                 
c2205                gpu-intera gpu:v100-p 32     480000     zen,prod                 
c2205                gpu-short  gpu:v100-p 32     480000     zen,prod                 
c2205                gpu        gpu:v100-p 32     480000     zen,prod                 
c2206                gpu-intera gpu:v100-p 32     480000     zen,prod                 
c2206                gpu-short  gpu:v100-p 32     480000     zen,prod                 
c2206                gpu        gpu:v100-p 32     480000     zen,prod                 
c2207                gpu-intera gpu:v100-p 32     480000     zen,prod                 
c2207                gpu-short  gpu:v100-p 32     480000     zen,prod                 
c2207                gpu        gpu:v100-p 32     480000     zen,prod                 
c4035                sharing    gpu:v100-s 28     578000     skylake_avx512,prod      
d1002                gpu-intera gpu:v100-s 28     191000     (null)                   
d1002                gpu-short  gpu:v100-s 28     191000     (null)                   
d1002                gpu        gpu:v100-s 28     191000     (null)                   
d1004                sharing    gpu:v100-s 28     187000     ib,skylake_avx512,prod   
d1007                gpu-intera gpu:v100-s 28     191000     (null)                   
d1007                gpu-short  gpu:v100-s 28     191000     (null)                   
d1007                gpu        gpu:v100-s 28     191000     (null)                   
d1009                gpu-intera gpu:v100-s 28     191000     (null)                   
d1009                gpu-short  gpu:v100-s 28     191000     (null)                   
(qml) [zhang.haoyu6@c3003 qTransformer_on_frustrated_Heisenberg_model]$ 

3. sinfo -p gpu -o "%20N %10c %10m %30G %25f" --Node | head -30
NODELIST             CPUS       MEMORY     GRES                           AVAIL_FEATURES           
c2204                32         480000     gpu:v100-pcie:2(S:0-1)         zen,prod                 
c2205                32         480000     gpu:v100-pcie:2(S:0-1)         zen,prod                 
c2206                32         480000     gpu:v100-pcie:2(S:0-1)         zen,prod                 
c2207                32         480000     gpu:v100-pcie:2(S:0-1)         zen,prod                 
d1002                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1007                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1009                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1010                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1011                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1012                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1013                28         191000     gpu:v100-sxm2:3(S:0-1)         (null)                   
d1015                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1017                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1019                28         191000     gpu:v100-sxm2:4(S:0-1)         (null)                   
d1020                28         187000     gpu:v100-sxm2:4(S:0-1)         ib,skylake_avx512,prod   
d1022                28         191000     (null)                         (null)                   
d1025                28         187000     gpu:t4:4(S:0-1)                ib,cascadelake,prod      
d1026                64         512000     gpu:a100:3                     ib,zen2,prod             
d1027                28         186000     gpu:v100-sxm2:4(S:0-1)         ib,skylake_avx512,prod   
d1028                64         512000     gpu:a100:4                     zen2,prod,ib,a100@80g    
d1029                64         512000     gpu:a100:4                     zen2,prod,ib,a100@80g    
d4052                128        512000     gpu:h200:8                     cascadelake,prod         
d4053                128        512000     gpu:h200:8                     cascadelake,prod         
d4054                128        512000     gpu:h200:8                     cascadelake,prod         
d4055                128        512000     gpu:h200:8                     cascadelake,prod         
(qml) [zhang.haoyu6@c3003 qTransformer_on_frustrated_Heisenberg_model]$ 

4. sinfo -p gpu --states=idle -o "%20N %10c %10m %30G" --Node
NODELIST             CPUS       MEMORY     GRES                          
c2204                32         480000     gpu:v100-pcie:2(S:0-1)        
c2205                32         480000     gpu:v100-pcie:2(S:0-1)        
c2206                32         480000     gpu:v100-pcie:2(S:0-1)        
c2207                32         480000     gpu:v100-pcie:2(S:0-1)        
d1010                28         191000     gpu:v100-sxm2:4(S:0-1)        
d1012                28         191000     gpu:v100-sxm2:4(S:0-1)        
d1013                28         191000     gpu:v100-sxm2:3(S:0-1)        
d1017                28         191000     gpu:v100-sxm2:4(S:0-1)        
d1019                28         191000     gpu:v100-sxm2:4(S:0-1)        
d1022                28         191000     (null)               

5. squeue -p gpu --format="%8i %20j %8u %8T %10M %6D %R" | head -20
JOBID    NAME                 USER     STATE    TIME       NODES  NODELIST(REASON)
4525177  eval_7b_all          kathuria PENDING  0:00       1      (QOSMaxGRESPerJob)
5686376  tak-az               navindgi PENDING  0:00       1      (Resources)
5687704  forge_bench          ravi.ka  PENDING  0:00       1      (Priority)
5687703  forge_bench          ravi.ka  PENDING  0:00       1      (Priority)
5687496  forge_bench          mahyavan PENDING  0:00       1      (Priority)
5687497  forge_bench          mahyavan PENDING  0:00       1      (Priority)
5687722  forge_bench          mahyavan PENDING  0:00       1      (Priority)
5687655  dream_acecode_mcts   biggs.s  PENDING  0:00       1      (Priority)
5687653  dream_acecode_mcts   biggs.s  PENDING  0:00       1      (Priority)
5687652  dream_acecode_mcts   biggs.s  PENDING  0:00       1      (Priority)
5687651  dream_acecode_mcts   biggs.s  PENDING  0:00       1      (Priority)
5688173  wrap                 chen.tia PENDING  0:00       1      (Priority)
5675763  val_ddim             sunger.e PENDING  0:00       1      (Priority)
5685665  grpo_inst            kazaka.w PENDING  0:00       1      (Priority)
5681987  val_ddim             sunger.e PENDING  0:00       1      (Priority)
5681990  val_ddim             sunger.e PENDING  0:00       1      (Priority)
5681989  val_ddim             sunger.e PENDING  0:00       1      (Priority)
5681988  val_ddim             sunger.e PENDING  0:00       1      (Priority)
5687075  pii_withA            furukawa PENDING  0:00       1      (QOSMaxJobsPerUserLimit)

6. lscpu | grep -E "Model name|Socket|Core|Thread|CPU\(s\)"
free -h
nvidia-smi 2>/dev/null || echo "No GPU on this node"
CPU(s):                             20
On-line CPU(s) list:                0-19
Model name:                         Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz
Thread(s) per core:                 1
Core(s) per socket:                 10
Socket(s):                          2
NUMA node0 CPU(s):                  0,2,4,6,8,10,12,14,16,18
NUMA node1 CPU(s):                  1,3,5,7,9,11,13,15,17,19
               total        used        free      shared  buff/cache   available
Mem:            62Gi        14Gi       9.8Gi        93Mi        38Gi        47Gi
Swap:           19Gi       264Mi        19Gi
No GPU on this node

7. scontrol show partition | grep -E "PartitionName|MaxTime|MaxNodes|DefaultTime" 
PartitionName=gpu
   DefaultTime=04:00:00 DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=UNLIMITED MaxTime=08:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
PartitionName=short
   DefaultTime=04:00:00 DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=2 MaxTime=2-00:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
PartitionName=sharing
   DefaultTime=NONE DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=2 MaxTime=01:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
PartitionName=gpu-short
   DefaultTime=01:00:00 DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=UNLIMITED MaxTime=02:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
PartitionName=gpu-interactive
   DefaultTime=01:00:00 DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=UNLIMITED MaxTime=02:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
(qml) [zhang.haoyu6@c3003 qTransformer_on_frustrated_Heisenberg_model]$ 