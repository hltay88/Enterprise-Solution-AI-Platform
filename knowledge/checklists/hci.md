# HCI / Hyperconverged Clarification Pack

Use for hyperconverged infrastructure, vSAN-style clusters, or HCI private-cloud builds.

## Cluster design
- Target cluster size (nodes), failure tolerance, and stretch/metro requirements?
- Compute vs storage-heavy workload mix and growth plan?
- GPU / special accelerator needs?

## Platform
- Preferred hypervisor / HCI stack constraints (or greenfield choice)?
- Existing licensing to reuse (hypervisor, Windows, SQL, etc.)?
- Network design for HCI east-west / storage traffic (dedicated switches)?

## Data protection
- Backup integration targets and backup window constraints?
- Snapshot / replication policy expectations?
- DR site topology and failover test cadence?

## Operations
- Who manages the HCI platform day-2?
- Lifecycle / firmware upgrade windows?
- Monitoring integration with existing NMS/ITSM?
