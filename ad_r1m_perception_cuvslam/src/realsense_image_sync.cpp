#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "rclcpp/logger.hpp"
#include "rclcpp_components/register_node_macro.hpp"

#include <deque>
#include <map>
#include <vector>
#include <string>
#include <cmath>

namespace camera_sync
{

    class MultiApproxSync : public rclcpp::Node
    {
    public:
        MultiApproxSync(const rclcpp::NodeOptions &options) : Node("realsense_image_sync", options)
        {

            this->declare_parameter("inter_message_slop", 0.02);
            this->declare_parameter("inner_message_slop", 0.02);
            this->declare_parameter("topics2subscribe", rclcpp::PARAMETER_STRING_ARRAY);
            this->declare_parameter("topics2publish", rclcpp::PARAMETER_STRING_ARRAY);

            this->get_parameter("inter_message_slop", inter_message_slop_);
            this->get_parameter("inner_message_slop", inner_message_slop_);
            this->get_parameter("topics2subscribe", topics2subscribe_);
            this->get_parameter("topics2publish", topics2publish_);

            params_sanity_check();

            // Creating all subscribers
            for (const auto &topic : topics2subscribe_)
            {
                auto sub = this->create_subscription<sensor_msgs::msg::Image>(
                    topic, 10,
                    [this, topic](const sensor_msgs::msg::Image::SharedPtr msg)
                    {
                        this->synchronize_images(msg, topic);
                    });

                subscribers_.push_back(sub);
                buffers_[topic] = std::deque<sensor_msgs::msg::Image::SharedPtr>();

                RCLCPP_INFO(this->get_logger(), "Image synchronization node subscribed to: %s", topic.c_str());
            }

            // Creating all (re-)publishers
            for (const auto &topic : topics2publish_)
            {
                auto pub = this->create_publisher<sensor_msgs::msg::Image>(topic, 10);
                publishers_.push_back(pub);

                RCLCPP_INFO(this->get_logger(), "Created sync publisher on topic: %s", topic.c_str());
            }
        }

    private:
        void params_sanity_check()
        {
            auto no_topics2subscribe = topics2subscribe_.size();
            auto no_topics2publish = topics2publish_.size();
            if (no_topics2subscribe != no_topics2publish)
            {
                RCLCPP_FATAL(this->get_logger(), "Number of suscribed topics should match the number of published topics.\n"
                                                 "no_topics2subscribe = %ld;\n no_topics2publish = %ld",
                                                no_topics2subscribe, no_topics2publish);
            }

            if (topics2subscribe_.empty())
            {
                RCLCPP_FATAL(this->get_logger(), "Subscription topic list should not be empty."
                                                 "\nGive a valid list of camera published topics.\nShutting down node...");
                rclcpp::shutdown();
                return;
            }
            if (topics2publish_.empty())
            {
                RCLCPP_FATAL(this->get_logger(), "Publisher topic list should not be empty."
                                                 "\nGive a valid list of topics to publish camera topics.\nShutting down node...");
                rclcpp::shutdown();
                return;
            }

            if (inter_message_slop_ < 0)
            {
                RCLCPP_WARN(this->get_logger(), "Biggest available stamp difference between images on different topics should be greater than zero."
                                                "\n inter_message_slop should be positive.\nTaking the absolute value...");
                inter_message_slop_ = fabs(inter_message_slop_);
            }

            if (inner_message_slop_ < 0)
            {
                RCLCPP_WARN(this->get_logger(), "Biggest available stamp difference between images on the same topic should be greater than zero."
                                                "\n inner_message_slop should be positive.\nTaking the absolute value...");
                inner_message_slop_ = fabs(inner_message_slop_);
            }
        }

        void synchronize_images(const sensor_msgs::msg::Image::SharedPtr msg,
                                const std::string &topic)
        {
            buffers_[topic].push_back(msg);

            // Remove old messages to keep buffer size small
            rclcpp::Time ref_time(msg->header.stamp);
            while (!buffers_[topic].empty())
            {
                rclcpp::Time buffered_msg_time(buffers_[topic].front()->header.stamp);
                if (fabs((ref_time - buffered_msg_time).seconds()) > inner_message_slop_)
                {
                    buffers_[topic].pop_front();
                }
                else
                {
                    break;
                }
            }

            // Try to find a synchronized set
            std::map<std::string, sensor_msgs::msg::Image::SharedPtr> candidate;
            bool all_found = true;
            for (auto &topic_and_msgs : buffers_)
            {
                const auto &topic_messages = topic_and_msgs.second;
                bool found = false;
                for (const auto &message : topic_messages)
                {
                    rclcpp::Time buffered_msg_time(message->header.stamp);
                    if (fabs((buffered_msg_time - ref_time).seconds()) < inter_message_slop_)
                    {
                        candidate[topic_and_msgs.first] = message;
                        found = true;
                        break;
                    }
                }
                if (!found)
                {
                    all_found = false;
                    break;
                }
            }

            if (all_found)
            {
                RCLCPP_INFO(this->get_logger(), "Synchronized group at ~ %.6f", ref_time.seconds());

                // Re-publishing synchronized group
                int publisher_idx = 0;
                for (auto &item : candidate)
                {
                    publishers_[publisher_idx]->publish(*item.second);
                    publisher_idx += 1;
                }
            }
        }
        std::map<std::string, std::deque<sensor_msgs::msg::Image::SharedPtr>> buffers_;

        std::vector<std::string> topics2subscribe_;
        std::vector<std::string> topics2publish_;
        std::vector<rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr> subscribers_;
        std::vector<rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr> publishers_;

        // The following can be set equal
        double inter_message_slop_; // inter topic time stamp difference
        double inner_message_slop_; // stamp difference between messages inside the same topic
    };
}

RCLCPP_COMPONENTS_REGISTER_NODE(camera_sync::MultiApproxSync)

// int main(int argc, char** argv) {
//     rclcpp::init(argc, argv);

//     auto sync_node = std::make_shared<MultiApproxSync>();

//     RCLCPP_INFO(sync_node->get_logger(),"Started image synchronization node...");

//     rclcpp::spin(sync_node);
//     rclcpp::shutdown();
//     return 0;
// }
