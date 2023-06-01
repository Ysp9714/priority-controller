# Controller 개발

# Admission

Admission 컨트롤러는 Kubernetes API 서버에 요청이 들어올 때 해당 요청을 가로채고 검증, 수정 또는 거부하는 역할을 한다. Volcano Admssion은 Volcano 스케줄러의 핵심 구성 요소로서, 작업의 자원 요청과 할당, 스케줄링 프로세스의 확장성과 유연성을 제공한다. 이를 통해 작업의 자원 이용률을 최적화하고, 클러스터 내의 작업들을 효과적으로 관리할 수 있다.

1. 자원 요청 검증: Volcano Admission은 사용자가 제출한 작업의 자원 요청을 검증한다. 요청한 CPU 또는 메모리 양이 유효한지 클러스터 내의 해당 자원이 충분한지 등을 확인한다. 이를 통해 올바른 자원 요청을 보장하고, 클러스터 내의 자원 이용을 최적화할 수 있다.
2. 자원 할당: Volcano Admission은 자원 요청이 유효하다고 판단되면 해당 작업에 대한 자원 할당을 수행한다. 이는 작업을 특정 노드에 스케줄링하고, 필요한 자원을 예약하며, 다른 작업들과의 자원 공유등을 조정하는 작업을 포함한다.
3. 스케줄러 훅: Volcano Admission은 스케줄링 프로세스 중에 호출되는 훅을 제공한다. 이 훅을 사용하면 사용자 정의 로직을 실행하여 작업의 스케줄링을 제어하거나 수정할 수 있다. 예를 들어 특정 작업이 스케줄링되기 전에 사전 처리 작업을 수행하거나 작업의 우선순위를 동적으로 조정하는 등의 작업을 수행할 수 있다.

# Controller

Controller는 Kubernetes 클러스터에서 작업의 스케줄링과 자원관리를 담당한다. 

1. 작업 스케줄링 : Volcano는 Queue 기반의 스케줄링을 수행하여 작업을 클러스터의 노드에 분배한다. 작업은 우선순위, 요구사항, 예약 가능한 시간대 등의 속성에 따라 스케줄링된다. 
2. 리소스 관리 : Volcano는 다양한 유형의 리소스 (CPU, 메모리, GPU)를 효율적으로 관리한다. 리소스 요구사항과 가용성을 기반으로 리소스를 할당하고 작업간의 리소스 격리르 유지한다.
3. 예약 제어 : Volcano는 예약 가능한 작업의 제어를 지원한다. 예약 가능한 작업은 특정 시간대에 실행될 수 있는 작업을 의미하며, 주기적인 배치 작업이나 특정 시간대에 리소스가 덜 사용되는 작업 등을 예약할 수 있다.
4. 유연한 정책 설정 : Volcano는 다양한 스케줄링 정책을 지원하여 작업의 실행 우선순위, 리소스 할당 규칙 예약 제어 등을 유연하게 설정할 수 있따. 이를 통해 사용자는 작업의 특정 요구사항에 따라 커스텀 스케줄링 정책을 정의할 수 있다.

# Volcano 스케줄러 사이클

1. Kubeflow에서 pipeline을 돌림
2. Argo workflow 형태로 작업이 시작됨
    - workflow 형태는 시작되면 Active 완료시 Succeeded 상태가 됨
3. schedulerName과 podPriorityClassName, queue 정보 등을 기입함
4. 생성된 workflow는 지정한 queue에 podgroup의 crd 형태로 시작된다.
5. 완료된 podgroup은 삭제되지 않는다.
    - podgroup은 namespace, queue별로 지정되서 들어간다.
    - 이걸 활용해서 penalty를 계산해야하나?
6. 패널티 계산 로직에 따라 패널티를 계산하고 완화한다.
    - 패널티는 priorityclass의 value를 통해 계산한다.

# 문제점

- 일단 argo workflow 형태에서 queue가 지정이 안 됨.
- queue를 지정안하면 무조건 default queue로 들어감. volcano 기본 설정
- queue field를 지정하는 방법을 생각해봐야함
- value update가 안됨. json 형태로 patch 불가능함. get은 불러와지는데 create, patch가 안됨.
    - 대안
        - PodGroup이 생성이 되면 총 상태가 3개로 나뉘어진다.
        - Pending → Running → Completed
        - 당연히 이 3가지 yaml의 형태는 같다 하지만 Running 상태가 되기 전 까지는 PriorityClassName의 value값을 참조해오지 않는다.
        - 즉, Pending 상태에서 value값이 1000 이었던 PriorityClass가 Running이 되기 전에 100이 되면 최종적으로 적용되는 value 값은 100이 된다.
        - 이를 활용하여 어떤 PodGroup의 상태가 Runnning이 되면 그 priorityclass의 value값에 penalty를 부여한 후 같은 이름의 priorityclass를 새로 만든다. 이를 순서로 나타내면 다음과 같다.
            - h-priority 라는 이름의 priorityclass가 있고 value값은 1000이다.
            - 이 priorityclass를 사용하는 podgroup이 만들어지고 Running 상태가 되면 value값에 변화가 일어난다.
            - 이 때 value값은 기존 1000에서 패널티를 제외한 값으로 갱신이 되는데 kubernetes에서 priorityclass는 변경이 불가능하다.
            - 따라서 기존의 h-priority 를 지우고 갱신한 value값을 넣어서 같은 이름으로 새로 만들어준다.
            - 그 다음부터 시작되는 podgroup은 새로운 h-priority의 value값을 참조해오게 된다.
- 이해가 안가는점 : cluster_scoped_custrom_resource가 delete, get은 되는데 왜 create가 안됨.