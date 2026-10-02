package optimizerv1_test

import (
	"context"
	"os"
	"testing"
	"time"

	optimizerv1 "github.com/fanscore-ch/optimizer/gen/go/optimizer/v1"
	"github.com/fanscore-ch/optimizer/gen/go/ortools/sat"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/protobuf/proto"
)

func TestPythonService(t *testing.T) {
	address := os.Getenv("OPTIMIZER_TEST_ADDRESS")
	if address == "" {
		t.Skip("OPTIMIZER_TEST_ADDRESS is not set")
	}
	connection, err := grpc.NewClient(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = connection.Close() })
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	health, err := grpc_health_v1.NewHealthClient(connection).Check(ctx, &grpc_health_v1.HealthCheckRequest{
		Service: "optimizer.v1.OptimizerService",
	})
	if err != nil || health.GetStatus() != grpc_health_v1.HealthCheckResponse_SERVING {
		t.Fatalf("health: %v, %v", health, err)
	}
	model := &sat.CpModelProto{
		Variables: []*sat.IntegerVariableProto{
			{Domain: []int64{0, 1}}, {Domain: []int64{0, 1}}, {Domain: []int64{0, 1}},
		},
		Constraints: []*sat.ConstraintProto{{
			Constraint: &sat.ConstraintProto_Linear{Linear: &sat.LinearConstraintProto{
				Vars: []int32{0, 1, 2}, Coeffs: []int64{6, 5, 3}, Domain: []int64{0, 8},
			}},
		}},
		Objective: &sat.CpObjectiveProto{
			Vars: []int32{0, 1, 2}, Coeffs: []int64{-6, -5, -3}, ScalingFactor: -1,
		},
	}
	response, err := optimizerv1.NewOptimizerServiceClient(connection).Solve(ctx, &optimizerv1.SolveRequest{
		Model:      model,
		Parameters: &sat.SatParameters{NumWorkers: proto.Int32(1), MaxTimeInSeconds: proto.Float64(1)},
	})
	if err != nil {
		t.Fatal(err)
	}
	result := response.GetResult()
	if result.GetStatus() != sat.CpSolverStatus_OPTIMAL || result.GetObjectiveValue() != 8 {
		t.Fatalf("unexpected result: %v", result)
	}
	solution := result.GetSolution()
	if len(solution) != 3 || solution[0] != 0 || solution[1] != 1 || solution[2] != 1 {
		t.Fatalf("unexpected solution: %v", solution)
	}
}
